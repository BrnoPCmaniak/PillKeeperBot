import os
import re
import logging

from telegram import (
    Emoji, ParseMode, ForceReply, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (
    Filters, Updater, CommandHandler, MessageHandler, CallbackQueryHandler)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                           '%(message)s',
                    level=logging.DEBUG)

# Define the different states a chat can be in
(
    MENU, ENTER_NAME, ENTER_TIMES, CHOOSE_REPEATING, ENTER_N_DAYS,
    ENTER_DATES) = range(6)
# Define choices for inline choose of repeating
EVERY_DAY, EVERY_N_DAY, WEEK_DAYS = [str(i) for i in range(3)]
# Define choices for work day select
(
    SUNDAY_ON, SUNDAY_OFF, MONDAY_ON, MODAY_OFF, TUESDAY_ON, TUESDAY_OFF,
    WEDNESDAY_ON, WEDNESDAY_OFF, THURSDAY_ON, THURSDAY_OFF, FRIDAY_ON,
    FRIDAY_OFF, SATURDAY_ON,
    SATURDAY_OFF, SAVE) = [str(i) for i in range(3, 18)]

# States are saved in a dict that maps chat_id -> state
state = dict()
# Sometimes you need to save data temporarily
context = dict()
days = dict()
# This dict is used to store the settings value for the chat.
# Usually, you'd use persistence for this (e.g. sqlite).
values = dict()
# Stack of last confirmations
confirmations = dict()


class Pill(object):
    times = None
    name = None
    user_id = None
    repeatEveryDay = False
    repeatEveryNthDay = None
    repeatDaysOfWeek = None

    def __init__(self, name, user_id):
        self.times = []
        self.user_id = user_id
        self.name = name

    def add_time(self, hour, minute):
        hour_i, minute_i = int(hour), int(minute)
        logging.debug("adding to \"%s\" time %d:%d" % (self.name, hour_i,
                                                       minute_i))
        self.times.append((hour_i, minute_i))

    def add_time_from_re_match(self, match):
        self.add_time(*match.group(1, 2))

    def __str__(self):
        return self.name + " " + str(self.times)


def add_and_return_context(name, user_id):
    p = Pill(name, user_id)
    context[user_id] = p
    return p


def save(user_id, p):
    if user_id not in values:
        values[user_id] = []
    values[user_id].append(p)
    del state[user_id]
    del context[user_id]
    logging.info("SAVED: %s" % str(p))


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
                        text="Please enter name of the pill:")


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
                        text="Please enter time/s in format 12:00 (GMT)")
    elif chat_state == ENTER_TIMES:
        m = re.match(r"^(\d{1,2}):(\d{1,2})$", update.message.text)
        if m is not None:
            pill = context.get(user_id, None)
            pill.add_time_from_re_match(m)
            bot.sendMessage(chat_id,
                            text="Got {0}:{1}\nPlease enter another time/s in "
                                 "format 12:00 (GMT) or enter "
                                 "/next".format(*m.group(1, 2)))
        else:
            bot.sendMessage(chat_id,
                            text="Invalid format please try again.\n"
                                 "Format must be hh:mm or h:mm or h:m in "
                                 "24h format!")
    elif chat_state == ENTER_N_DAYS:
        m = re.match(r"^(\d+)$", update.message.text)
        if m is not None:
            pill = context.get(user_id, None)
            pill.repeatEveryNthDay = int(m.group(1))
            save(user_id, pill)
            bot.sendMessage(
                chat_id,
                text="Finished. Annoucement will repeat every "
                     "%d day/s" % int(m.group(1)))
        else:
            bot.sendMessage(chat_id,
                            text="Invalid format please try again.\n"
                                 "Format must be a number!")


def next_state(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    chat_state = state.get(user_id, MENU)
    if chat_state == ENTER_TIMES:
        pill = context.get(user_id, None)
        if len(pill.times) != 0:
            state[user_id] = CHOOSE_REPEATING
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Every day", callback_data=EVERY_DAY)],
                 [InlineKeyboardButton("Every nth day",
                                       callback_data=EVERY_N_DAY)],
                 [InlineKeyboardButton("Week days", callback_data=WEEK_DAYS)]])
            bot.sendMessage(chat_id,
                            text="Which type of day repeating do you want?",
                            reply_markup=reply_markup)
        else:
            bot.sendMessage(chat_id,
                            text="ERROR: no time added to pill.")
    else:
        bot.sendMessage(chat_id, text="ERROR: nothing to do.")


def callback_handler(bot, update):
    query = update.callback_query
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    text = query.data
    user_state = state.get(user_id, MENU)
    user_context = context.get(user_id, None)

    # Check if we are waiting for confirmation and the right user answered
    if user_state == CHOOSE_REPEATING:
        if text == EVERY_DAY:
            user_context.repeatEveryDay = True
            save(user_id, user_context)
            bot.editMessageText(
                text="Finished. Repeating annoucement every day.",
                chat_id=chat_id,
                message_id=query.message.message_id)
        elif text == EVERY_N_DAY:
            state[user_id] = ENTER_N_DAYS
            bot.editMessageText(text="Please enter number of days:",
                                chat_id=chat_id,
                                message_id=query.message.message_id)
        elif text == WEEK_DAYS:
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Sun - OFF",
                                       callback_data=SUNDAY_ON),
                  InlineKeyboardButton("Mon - OFF",
                                       callback_data=MONDAY_ON),
                  InlineKeyboardButton("Tue - OFF",
                                       callback_data=TUESDAY_ON)],
                 [InlineKeyboardButton("Wed - OFF",
                                       callback_data=WEDNESDAY_ON),
                  InlineKeyboardButton("Thu - OFF",
                                       callback_data=THURSDAY_ON),
                  InlineKeyboardButton("Fri - OFF",
                                       callback_data=FRIDAY_ON)],
                 [InlineKeyboardButton("Sat - OFF",
                                       callback_data=SATURDAY_ON),
                  InlineKeyboardButton("Save", callback_data=SAVE)]])
            bot.editMessageText(
                text="Choose whcih days you want to be annouced.",
                chat_id=chat_id,
                message_id=query.message.message_id,
                reply_markup=reply_markup)


def hello(bot, update):
    bot.sendMessage(update.message.chat_id,
                    text='Hello {0}'.format(
                        update.message.from_user.first_name))


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))


def list_pills(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    bot.sendMessage(
        chat_id,
        text="List:%s" % (
            "".join(["\n * " + str(i) for i in values.get(user_id, [])]))
        )

updater = Updater(os.environ.get('TOKEN'))

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('new', new_pill))
updater.dispatcher.add_handler(CommandHandler('list', list_pills))
updater.dispatcher.add_handler(CommandHandler('next', next_state))
updater.dispatcher.add_handler(MessageHandler([Filters.text], entered_value))
updater.dispatcher.add_handler(CallbackQueryHandler(callback_handler))
updater.dispatcher.add_handler(CommandHandler('hello', hello))
updater.dispatcher.add_error_handler(error)

updater.start_polling()
updater.idle()
