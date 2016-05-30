import logging
import re
import os
from telegram import Emoji, ForceReply, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    CallbackQueryHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                           '%(message)s',
                    level=logging.DEBUG)

# Define the different states a chat can be in
MENU, ENTER_NAME, ENTER_TIMES, CHOSE_REPEATING, ENTER_DATES = range(5)

# States are saved in a dict that maps chat_id -> state
state = dict()
# Sometimes you need to save data temporarily
context = dict()
# This dict is used to store the settings value for the chat.
# Usually, you'd use persistence for this (e.g. sqlite).
values = dict()
# Stack of last confirmations
confirmations = dict()


class Pill(object):
    times = []
    name = None
    user_id = None
    repeatEveryDay = False
    repeatEveryNthDay = None
    repeatDaysOfWeek = []

    def __init__(self, name, user_id):
        self.user_id = user_id
        self.name = name

    def add_time(self, hour, minute):
        self.times.append((hour, minute))

    def add_time_from_re_match(self, match):
        self.add_time(*match.group(1, 2))


def add_and_return_context(name, user_id):
    p = Pill(name, user_id)
    context[user_id] = p
    return p


def start(bot, update):
    bot.sendMessage(update.message.chat_id,
                    text="Hi, I'm here to help you not forgetting getting the "
                         "pills!\nUse /new to add new pill.")


# Example handler. Will be called on the /set command and on regular messages
def new_pill(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_state = state.get(chat_id, MENU)

    if user_state == MENU:
        state[user_id] = ENTER_NAME  # set the state
        bot.sendMessage(chat_id,
                        text="Please enter name of the pill:",
                        reply_markup=ForceReply())


def entered_value(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    chat_state = state.get(user_id, MENU)

    # Check if we are waiting for input
    if chat_state == ENTER_NAME:
        state[user_id] = ENTER_TIMES

        # Save the user id and the answer to context
        pill = add_and_return_context(update.message.text, user_id)
        bot.sendMessage(chat_id,
                        text="Please enter time/s in format 12:00 (GMT)",
                        reply_markup=ForceReply())
    elif chat_state == ENTER_TIMES:
        m = re.match(r"^(\d{1,2}):(\d{1,2})$", update.message.text)
        if m is not None:
            pill = context.get(user_id, None)
            pill.add_time_from_re_match(m)
            bot.sendMessage(chat_id,
                            text="Got {0}:{1} Please enter another time/s in "
                                 "format 12:00 (GMT) or enter "
                                 "/next".format(*m.group(1, 2)),
                            reply_markup=ForceReply())
        else:
            bot.sendMessage(chat_id,
                            text="Invalid format please try again.",
                            reply_markup=ForceReply())


def next_state(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    chat_state = state.get(user_id, MENU)

    if chat_state == ENTER_TIMES:
        state[user_id] = CHOSE_REPEATING
        bot.sendMessage(chat_id, text="Which type of day repeating do "
                                      "you want?")
    else:
        bot.sendMessage(chat_id, text="ERROR: nothing to do.")


def hello(bot, update):
    bot.sendMessage(update.message.chat_id,
                    text='Hello {0}'.format(
                        update.message.from_user.first_name))


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))

updater = Updater(os.environ.get('TOKEN'))

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('new', new_pill))
updater.dispatcher.add_handler(CommandHandler('next', next_state))
updater.dispatcher.add_handler(MessageHandler([Filters.text], entered_value))
updater.dispatcher.add_handler(CommandHandler('hello', hello))
updater.dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()
