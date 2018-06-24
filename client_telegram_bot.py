import re
import os
import json
import random
import logging

from collections import Counter
from telegram.ext import Updater
from html import escape
from datetime import datetime
from telegram import ParseMode
from telegram.ext import MessageHandler, CommandHandler, Filters

# Configuration
BOTNAME = ''
TOKEN = '581070543:AAHMQr4wMon0GBylJGfMBifFCfQqKYvCTI4'
# BOTAN_TOKEN = 'BOTANTOKEN'
DEFAULTADMINID = 268241452

# Set up logging
root = logging.getLogger()
root.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s \
                    - %(message)s')

logger = logging.getLogger(__name__)

# set updater and dispatcher
updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher
bot_jobs = updater.job_queue

global message_to_send
global user_logs_json
global config_settings
config_settings = {
    'welome_message': ['Hello $username! Welcome to $title'],
    'spam_words': [],
    'bot_admins': [DEFAULTADMINID],
    'daily_messages': {},
    'weekly_messages': {}
}
print(type(config_settings))
print(config_settings)
user_logs_json = {}
# user logs file
if not os.path.exists('users_activity.json'):
    print("creating log file")
    file = open('users_activity.json', 'w+')
    file.write(str(user_logs_json))
    file.close()
if not os.path.exists('config_file.json'):
    print("creating config file")
    file = open('config_file.json', 'w+')
    r = json.dumps(config_settings)
    file.write(str(r))
    file.close()

with open('config_file.json', 'r') as infile:
    print("json loaded to memory")
    config_settings = json.load(infile)
    print(config_settings)

with open('users_activity.json', 'r') as infile:
    print("loading configursation settings")
    user_logs_json = json.load(infile)
    print(user_logs_json)


def check_if_bot_admin(user_id):
    if user_id in config_settings["bot_admins"]:
        return True
    else:
        return False


def get_my_id(bot, update):
    bot.send_message(
        chat_id=update.message.chat_id, text=update.message.from_user.id)


def set_group(bot, update):
    "set the group id to where the bot belongs"
    global config_settings
    if check_if_bot_admin(update.message.from_user.id):
        group_chat_id = update.message.chat_id
        config_settings["group_chat_id"] = group_chat_id
        with open('config_file.json', 'w') as infile:
            infile.write(json.dumps(config_settings, indent=4))
        bot.send_message(
            chat_id=update.message.from_user.id,
            text="Group id was set successfully")
    else:
        logger.info('group not set since user not admin')


def add_weekly_message(bot, update, args):
    """
    add a message to the weekly schedule
    """
    global config_settings
    weekly_messages_dict = config_settings["weekly_messages"]
    sep_pos = args.index("!")
    weekly_time_string = str(args[:sep_pos][0]) + " " + str(
        args[:sep_pos][1]) + " " + str(args[:sep_pos][2])
    print(weekly_time_string)
    weekly_time = datetime.strptime(weekly_time_string, '%B %d, %H:%M')
    day_of_week = weekly_time.strftime('%A')
    time_of_message = str(weekly_time.hour) + ":" + str(weekly_time.minute)
    full_weekly_time = day_of_week + " " + time_of_message
    weekly_message = args[sep_pos + 1:]
    weekly_messages_dict[full_weekly_time] = " ".join(weekly_message)
    config_settings["weekly_messages"] = weekly_messages_dict
    with open('config_file.json', 'w') as infile:
        infile.write(json.dumps(config_settings, indent=4))
    bot.send_message(
        chat_id=update.message.from_user.id,
        text="Weekly message was added successfully")


def add_daily_message(bot, update, args):
    """
    add a message to the weekly schedule
    """
    global config_settings
    daily_messages_dict = config_settings["daily_messages"]
    sep_pos = args.index("!")
    daily_time_string = str(args[:sep_pos][0])
    print(type(daily_time_string))
    daily_time = str(datetime.strptime(daily_time_string, '%H:%M').time())
    print(daily_time)
    daily_message = args[sep_pos + 1:]
    daily_messages_dict[daily_time] = " ".join(daily_message)
    config_settings["daily_messages"] = daily_messages_dict
    with open('config_file.json', 'w') as infile:
        infile.write(json.dumps(config_settings, indent=4))
    bot.send_message(
        chat_id=update.message.from_user.id,
        text="Daily message was set successfully")


def add_bot_admin(bot, update, args):
    """
    add bot admin
    """
    global config_settings
    if check_if_bot_admin(update.message.from_user.id):
        user_id = args[0]
        if int(user_id) not in config_settings["bot_admins"]:
            config_settings["bot_admins"].append(int(user_id))
            with open('config_file.json', 'w') as infile:
                infile.write(json.dumps(config_settings, indent=4))
            bot.send_message(
                chat_id=update.message.chat_id,
                text="new bot admin succesfully added")


def list_bot_admins(bot, update):
    global config_settings
    if check_if_bot_admin(update.message.from_user.id):
        bot_message = ""
        for admin_id in config_settings["bot_admins"]:
            bot_message += str(
                bot.getChatMember(update.message.chat_id, admin_id)
                .user.first_name) + "  " + str(
                    bot.getChatMember(
                        update.message.chat_id,
                        admin_id).user.last_name) + " " + str(admin_id) + '\n'
        bot.send_message(chat_id=update.message.chat_id, text=bot_message)


def del_bot_admin(bot, update, args):
    global config_settings
    if check_if_bot_admin(update.message.from_user.id):
        del_admin_id = args[0]
        if int(del_admin_id) in config_settings["bot_admins"]:
            bot_admin_list = config_settings["bot_admins"]
            bot_admin_list.remove(int(del_admin_id))
            with open('config_file.json', 'w') as infile:
                infile.write(json.dumps(config_settings, indent=4))
            bot.send_message(
                chat_id=update.message.chat_id,
                text="bot admin succesfully deleted")


# Welcome a user to the chat
def welcome(bot, update):
    """ Welcomes a user to the chat """

    message = update.message
    chat_id = message.chat.id
    logger.info('%s joined to chat %d (%s)' %
                (escape(message.new_chat_members[-1].first_name), chat_id,
                 escape(message.chat.title)))

    # You can edit this to a custom message
    text = random.choice(config_settings["welome_message"])

    # Use default message if there's no custom one set
    if text is None:
        text = 'Hello $username! Welcome to $title'

    # Replace placeholders and send message
    text = text.replace('$username',
                        message.new_chat_members[-1].first_name).replace(
                            '$title', message.chat.title)
    bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)


def set_welcome_message(bot, update, args):
    if check_if_bot_admin(update.message.from_user.id):
        global config_settings
        """
        sets the welcome message
        """
        print(args)
        new_message = " ".join(args)
        if new_message:
            message_list = config_settings["welome_message"]
            if len(message_list) > 5:
                del message_list[1]
                message_list.append(new_message)
            else:
                message_list.append(new_message)
            with open('config_file.json', 'w') as infile:
                infile.write(json.dumps(config_settings, indent=4))
            bot.send_message(
                chat_id=update.message.chat_id,
                text="new welcome message succesfully set!")
        else:
            bot.send_message(
                chat_id=update.message.chat_id,
                text="Cannot set empty welcome message!")


def add_spam_word(bot, update, args):
    """
    Add new spam word to dictionary
    """
    global config_settings
    if check_if_bot_admin(update.message.from_user.id):
        new_spam_word = " ".join(args)
        if new_spam_word:
            spam_list = config_settings["spam_words"]
            spam_list.append(new_spam_word)
            config_settings["spam_words"] = spam_list
            with open('config_file.json', 'w') as infile:
                infile.write(json.dumps(config_settings, indent=4))
            bot.send_message(
                chat_id=update.message.chat_id,
                text="New spam word succesfully set!")
        else:
            bot.send_message(
                chat_id=update.message.chat_id,
                text="Cannot add empty spam word!")


def remove_spam_word(bot, update, args):
    """
    Remove spam word from dictionary
    """
    global config_settings
    if check_if_bot_admin(update.message.from_user.id):
        spam_word = " ".join(args)
        if spam_word:
            spam_list = config_settings["spam_words"]
            spam_list.remove(spam_word)
            config_settings["spam_words"] = spam_list
            with open('config_file.json', 'w') as infile:
                infile.write(json.dumps(config_settings, indent=4))
            bot.send_message(
                chat_id=update.message.chat_id,
                text="Spam word removed from dictionary!")
        else:
            bot.send_message(
                chat_id=update.message.chat_id,
                text="Cannot remove empty spam word!")


def list_spam_words(bot, update):
    if check_if_bot_admin(update.message.from_user.id):
        global config_settings
        spam_list = config_settings["spam_words"]
        spam_string = " ".join(spam_list)
        bot.send_message(chat_id=update.message.chat_id, text=spam_string)


def help_menu(bot, update):
    """
    Displays the help menu
    """
    if check_if_bot_admin(update.message.from_user.id):
        menu_message = """ BOT HELP MENU:
        /addspam <spamword> - This command helps to add a new spam word into the bots memory
        /setwelcome <welcomemessage> - This command allows you to customize the welcome message. Your message should be like this 'Hello $username! Welcome to $title'
        /mostactive - This command will give you the list of most active users in the group
        /set <seconds> <message> - This command will allows you to set a message to be displayed after the seconds set
        /listspamwords - shows the words that have been added to the spam dictionary
        /delspam <spamword> - deletes a spam word from the spam dictionary
        /addbotadmin <userid> - adds a user wh can interact with the bot
        /listbotadmins - list users who have right to interact with the bot with their user IDs
        /delbotadmin <userID> - deletes a user from the lis of users who can interact with the bot
        /getmyid - tool to show your user ID
        /addweeklymessage - Month date, HH:MM ! Message (The month and date should start followed by the message)
        /adddailylymessage - HH:MM ! Message (Only time to show the message should be specified)
        /listweeklymessages - shows the weekly messages in schedule
        /listdailymessages - shows the daily messages in schedule
        /deldailymessage [time]- deletes daily message from schedule
        /delweeklymessage [time]- deletes weekly message from schedule 
        """
        bot.send_message(chat_id=update.message.chat_id, text=menu_message)


def empty_message(bot, update):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member, someone left the chat or if the bot has been added somewhere.
    """
    if update.message.new_chat_members[-1] is not None:
        # Bot was added to a group chat
        if update.message.new_chat_members[-1].username != BOTNAME:
            return welcome(bot, update)


def check_spam(bot, update):
    global user_logs_json
    global config_settings
    spam_words_list = config_settings["spam_words"]
    print(update.message.text)
    text = update.message.text
    # check if text is a spam
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]| \
                     [$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    contains_spam = False
    for letter in text.split():
        if letter in " ".join(spam_words_list):
            contains_spam = True
            if contains_spam:
                print(letter)
    # check if any spam found
    if urls:
        # delete spam message
        bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id)
    elif contains_spam:
        # delete spam message
        bot.delete_message(
            chat_id=update.message.chat_id,
            message_id=update.message.message_id)
    else:  # add user activity log
        with open('users_activity.json', 'r') as infile:
            print(infile)
            user_logs_json = {}
            user_logs_json = json.load(infile)
            print(user_logs_json.keys())
            print(user_logs_json)
            if isinstance(user_logs_json, dict):
                json_keys = list(user_logs_json.keys())
                json_keys = [str(i) for i in json_keys]
                print(json_keys)
                if str(update.message.from_user.id) in json_keys:
                    user_logs_json[update.message.from_user.id] = str(
                        int(user_logs_json[str(update.message.from_user.id)]) +
                        1)
                else:
                    print("adding new member to database")
                    user_logs_json.update({
                        str(update.message.from_user.id): '1'
                    })

        with open('users_activity.json', 'w') as infile:
            infile.write(json.dumps(user_logs_json, indent=4))


def check_active_users(bot, update):
    # get active users in a group
    global user_logs_json
    if check_if_bot_admin(update.message.from_user.id):
        print(user_logs_json)
        users_message = 'no active users yet'
        with open('users_activity.json', 'r') as infile:
            print(infile)
            if user_logs_json:
                user_logs_json = json.load(infile)
                sorted_users = Counter(user_logs_json)
                top_five = sorted_users.most_common(5)
                print(top_five)
                users_message = ''
                for user_id in top_five:
                    print(user_id[0])
                    users_message += str(
                        bot.getChatMember(update.message.chat_id, user_id[0])
                        .user.first_name) + "  " + str(
                            bot.getChatMember(
                                update.message.chat_id,
                                user_id[0]).user.last_name) + '\n'
        bot.send_message(chat_id=update.message.chat_id, text=users_message)


def timed_messages(bot, job):
    """Send timed messages."""
    global config_settings
    # print(config_settings.keys())
    if 'group_chat_id' not in config_settings.keys():
        # print("group chat id does not exist yet")
        logger.info(
            'group chat id does not exist yet hence message sent to senders chat'
        )
        bot.send_message(job.context, text=message_to_send)
    else:
        bot.send_message(
            chat_id=int(config_settings["group_chat_id"]),
            text=message_to_send)
        logger.info('timed message sent to group ID')


def set_timer(bot, update, args, job_queue, chat_data):
    global message_to_send
    """Add a job to the queue."""
    if check_if_bot_admin(update.message.from_user.id):
        chat_id = update.message.chat_id
        try:
            # args[0] should contain the time for the timer in seconds
            due = int(args[0])
            message_to_send = ' '.join(args[1:])
            print(message_to_send)
            if due < 0:
                update.message.reply_text('Sorry we can not go back to past!')
                return

            # Add job to queue
            job = job_queue.run_once(timed_messages, due, context=chat_id)
            chat_data['job'] = job

            update.message.reply_text('Timed message successfully set!')

        except (IndexError, ValueError):
            update.message.reply_text('Usage: /set <seconds>')


def check_messages_to_send(bot, job):
    global config_settings
    days = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
        "Sunday"
    ]
    # print("checking messages")
    daily_messages_dict = config_settings["daily_messages"]
    message_times = daily_messages_dict.keys()
    # loop through message times to check for any message supposed to be send
    for times in message_times:
        message_time = datetime.strptime(times, '%H:%M:%S').time()
        if message_time.hour == datetime.now().hour:
            if message_time.minute == datetime.now().minute:
                if int(datetime.now().second) < 40:
                    bot.send_message(
                        chat_id=int(config_settings["group_chat_id"]),
                        text=daily_messages_dict[times])
    weekly_messages_dict = config_settings["weekly_messages"]
    weekly_message_times = weekly_messages_dict.keys()
    for weekly_times in weekly_message_times:
        weekly_times_group = weekly_times.split()
        day_number = datetime.today().weekday()
        if weekly_times_group[0] == days[day_number]:
            # print(weekly_times_group[0] + " has a message")
            actual_message_time = datetime.strptime(weekly_times_group[1],
                                                    '%H:%M').time()
            if actual_message_time.hour == datetime.now().hour:
                # print("hour has a message")
                if actual_message_time.minute == datetime.now().minute:
                    print("Minute has a message")
                    if int(datetime.now().second) < 40:
                        bot.send_message(
                            chat_id=int(config_settings["group_chat_id"]),
                            text=weekly_messages_dict[weekly_times])


def list_weekly_messages(bot, update):
    """
    list all weekly messages
    """
    global config_settings
    weekly_messages = config_settings["weekly_messages"]
    weekly_messages_string = ""
    if weekly_messages:
        for k in weekly_messages.iterkeys():
            weekly_messages_string += str(k) + "\t"
            weekly_messages_string += str(weekly_messages[k]) + "\n" 
    else:
        weekly_messages_string = "No Weekly Messages Added Yet"
    bot.send_message(chat_id=update.message.chat_id, text=weekly_messages_string)

def list_daily_messages(bot, update):
    """
    list all weekly messages
    """
    global config_settings
    daily_messages = config_settings["daily_messages"]
    daily_messages_string = ""
    if daily_messages:
        for k in daily_messages.iterkeys():
            daily_messages_string += str(k) + "\t"
            daily_messages_string += str(daily_messages[k]) + "\n"   
    else:
        daily_messages_string = "No Daily Messages Added Yet"        
    bot.send_message(chat_id=update.message.chat_id, text=daily_messages_string)

def delete_daily_message(bot, update, args):
    """
    list all weekly messages
    """
    global config_settings
    message_key = " ".join(args)
    daily_messages = config_settings["daily_messages"]
    if daily_messages:
        if message_key:
            if message_key in daily_messages.keys():
                daily_messages.pop(message_key, None)
                config_settings["daily_messages"] = daily_messages
                with open('config_file.json', 'w') as infile:
                    infile.write(json.dumps(config_settings, indent=4))
                bot.send_message(chat_id=update.message.chat_id, text="Daily message deleted")
            else:
                bot.send_message(chat_id=update.message.chat_id, text="You tried to delete a message not in schedule")

    else:
        bot.send_message(chat_id=update.message.chat_id, text="You tried to delete a message not in schedule")


def delete_weekly_message(bot, update, args):
    """
    list all weekly messages
    """
    global config_settings
    message_key = " ".join(args)
    weekly_messages = config_settings["weekly_messages"]
    print(message_key)
    if weekly_messages:
        if message_key:
            if message_key in weekly_messages.keys():
                weekly_messages.pop(message_key, None)
                config_settings["weekly_messages"] = weekly_messages
                with open('config_file.json', 'w') as infile:
                    infile.write(json.dumps(config_settings, indent=4))
                bot.send_message(chat_id=update.message.chat_id, text="Weekly message deleted")
            else:
                bot.send_message(chat_id=update.message.chat_id, text="You tried to delete a message not in schedule")    
    else:
        bot.send_message(chat_id=update.message.chat_id, text="You tried to delete a message not in schedule")
        


def unset(bot, update, chat_data):
    """Remove the job if the user changed their mind."""
    if check_if_bot_admin(update.message.from_user.id):
        if 'job' not in chat_data:
            update.message.reply_text('You have no active timer')
            return

        job = chat_data['job']
        job.schedule_removal()
        del chat_data['job']

        update.message.reply_text('Timer successfully unset!')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


messages_job = bot_jobs.run_repeating(
    check_messages_to_send, interval=30, first=0)
welcome_handler = MessageHandler(Filters.status_update, empty_message)
spam_handler = MessageHandler(Filters.text, check_spam)
set_handler = CommandHandler(
    "set", set_timer, pass_args=True, pass_job_queue=True, pass_chat_data=True)
active_users_handler = CommandHandler("mostactive", check_active_users)
set_spam_handler = CommandHandler("addspam", add_spam_word, pass_args=True)
del_spam_handler = CommandHandler("delspam", remove_spam_word, pass_args=True)
set_welcome_handler = CommandHandler(
    "setwelcome", set_welcome_message, pass_args=True)
help_menu_handler = CommandHandler("botmenu", help_menu)
list_spam_handler = CommandHandler("listspamwords", list_spam_words)
add_bot_admin_handler = CommandHandler(
    "addbotadmin", add_bot_admin, pass_args=True)
list_bot_admins_handler = CommandHandler("listbotadmins", list_bot_admins)
del_bot_admin = CommandHandler("delbotadmin", del_bot_admin, pass_args=True)
get_my_id_handler = CommandHandler("getmyid", get_my_id)
set_group_handler = CommandHandler("setgroup", set_group)
add_daily_message_handler = CommandHandler(
    "adddailymessage", add_daily_message, pass_args=True)
add_weekly_message_handler = CommandHandler(
    "addweeklymessage", add_weekly_message, pass_args=True)
del_daily_message_handler = CommandHandler(
    "deldailymessage", delete_daily_message, pass_args=True)
del_weekly_message_handler = CommandHandler(
    "delweeklymessage", delete_weekly_message, pass_args=True)    
list_daily_messages_handler = CommandHandler("listdailymessages", list_daily_messages)
list_weekly_messages_handler = CommandHandler("listweeklymessages", list_weekly_messages)
dispatcher.add_handler(welcome_handler)
dispatcher.add_handler(spam_handler)
dispatcher.add_handler(set_handler)
dispatcher.add_handler(active_users_handler)
dispatcher.add_handler(set_spam_handler)
dispatcher.add_handler(set_welcome_handler)
dispatcher.add_handler(help_menu_handler)
dispatcher.add_handler(del_spam_handler)
dispatcher.add_handler(list_spam_handler)
dispatcher.add_handler(add_bot_admin_handler)
dispatcher.add_handler(list_bot_admins_handler)
dispatcher.add_handler(del_bot_admin)
dispatcher.add_handler(get_my_id_handler)
dispatcher.add_handler(set_group_handler)
dispatcher.add_handler(CommandHandler("unset", unset, pass_chat_data=True))
dispatcher.add_handler(add_daily_message_handler)
dispatcher.add_handler(add_weekly_message_handler)
dispatcher.add_handler(list_daily_messages_handler)
dispatcher.add_handler(list_weekly_messages_handler)
dispatcher.add_handler(del_daily_message_handler)
dispatcher.add_handler(del_weekly_message_handler)
# log all errors
dispatcher.add_error_handler(error)
updater.start_polling()
updater.idle()
