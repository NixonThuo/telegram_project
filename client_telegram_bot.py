import re
import os
import json
import logging

from collections import Counter
from telegram.ext import Updater
from html import escape
from telegram import ParseMode
from telegram.ext import MessageHandler, CommandHandler, Filters

# Configuration
BOTNAME = 'nickmillbot'
TOKEN = '581070543:AAHMQr4wMon0GBylJGfMBifFCfQqKYvCTI4'
BOTAN_TOKEN = 'BOTANTOKEN'

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

global message_to_send
global user_logs_json
global config_settings
config_settings = {
    'welome_message': 'Hello $username! Welcome to $title',
    'spam_words': [],
    'bot_admins': [268241452]
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
    if user_id in config_settings['bot_admins']:
        return True
    else:
        return False


# Welcome a user to the chat
def welcome(bot, update):
    """ Welcomes a user to the chat """

    message = update.message
    chat_id = message.chat.id
    logger.info('%s joined to chat %d (%s)' %
                (escape(message.new_chat_members[-1].first_name), chat_id,
                 escape(message.chat.title)))

    # You can edit this to a custom message
    text = config_settings["welome_message"]

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
            config_settings["welome_message"] = new_message
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
                chat_id=update.message.chat_id, text="Cannot add empty spam word!")


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
                            bot.getChatMember(update.message.chat_id,
                                              user_id[0]).user.last_name) + '\n'
        bot.send_message(chat_id=update.message.chat_id, text=users_message)


def timed_messages(bot, job):
    """Send timed messages."""
    bot.send_message(job.context, text=message_to_send)


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
dispatcher.add_handler(welcome_handler)
dispatcher.add_handler(spam_handler)
dispatcher.add_handler(set_handler)
dispatcher.add_handler(active_users_handler)
dispatcher.add_handler(set_spam_handler)
dispatcher.add_handler(set_welcome_handler)
dispatcher.add_handler(help_menu_handler)
dispatcher.add_handler(del_spam_handler)
dispatcher.add_handler(list_spam_handler)
dispatcher.add_handler(CommandHandler("unset", unset, pass_chat_data=True))
# log all errors
dispatcher.add_error_handler(error)
updater.start_polling()
updater.idle()
