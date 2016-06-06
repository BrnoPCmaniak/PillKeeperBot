import os
import re
import logging

from telegram import (
    Emoji, ParseMode, ForceReply, KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (
    Filters, Updater, CommandHandler, MessageHandler, CallbackQueryHandler)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# Ensure settings are read
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Your application specific imports
from data.models import *

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - '
                           '%(message)s',
                    level=logging.DEBUG)

# Define the different states a chat can be in
(
    MENU, ENTER_NAME, ENTER_TIMES, CHOOSE_REPEATING, ENTER_N_DAYS,
    ENTER_DATES) = range(6)
# Define choices for inline choose of repeating
EVERY_DAY, EVERY_N_DAY, WEEK_DAYS, SAVE = [str(i) for i in range(4)]

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

def gen_reply_week_day_markup(user_state):
    """
    example:
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
    """
    def get_day(pill, day):
        try:
            WeekDaysRepetion.objects.get(pill=pill, day=day)
            found = True
        except WeekDaysRepetion.DoesNotExist:
            found = False
        found_str = " - ON" if found else " - OFF"
        found_int = "0" if found else "1"
        print(str(day), found_int.__class__, DAYS[day].__class__,found_str.__class__)
        return InlineKeyboardButton(DAYS[day] + found_str,
                                    callback_data=str(day) + found_int)

    p = user_state.pill

    return InlineKeyboardMarkup(
        [[get_day(p, 6), get_day(p, 0), get_day(p, 1)],
         [get_day(p, 2), get_day(p, 3), get_day(p, 4)],
         [get_day(p, 5), InlineKeyboardButton("Save", callback_data=SAVE)]])

def start(bot, update):
    bot.sendMessage(update.message.chat_id,
                    text="Hi, I'm here to help you not forgetting getting the "
                         "pills!\nUse /new to add new pill.")


def new_pill(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_state = State.get_state(chat_id, user_id)

    if user_state.state == MENU:
        user_state.state = ENTER_NAME  # set the state
        user_state.save()
        bot.sendMessage(chat_id,
                        text="Please enter name of the pill:")


def entered_value(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_state = State.get_state(chat_id, user_id)

    # Check if we are waiting for input
    if user_state.state == ENTER_NAME:
        user_state.state = ENTER_TIMES

        # Save the user id and the answer to context
        pill = Pill(name=update.message.text, user_id=user_id, chat_id=chat_id)
        pill.save()
        user_state.pill = pill
        user_state.save()
        bot.sendMessage(chat_id,
                        text="Please enter time/s in format 12:00 (GMT)")
    elif user_state.state == ENTER_TIMES:
        m = re.match(r"^(\d{1,2}):(\d{1,2})$", update.message.text)
        if m is not None:
            user_state.pill.add_time_from_re_match(m)
            bot.sendMessage(chat_id,
                            text="Got {0}:{1}\nPlease enter another time/s in "
                                 "format 12:00 (GMT) or enter "
                                 "/next".format(*m.group(1, 2)))
        else:
            bot.sendMessage(chat_id,
                            text="Invalid format please try again.\n"
                                 "Format must be hh:mm or h:mm or h:m in "
                                 "24h format!")
    elif user_state.state == ENTER_N_DAYS:
        m = re.match(r"^(\d+)$", update.message.text)
        if m is not None:
            RepeatEveryNthDay(pill=user_state.pill, n=int(m.group(1))).save()
            user_state.clean()
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
    user_state = State.get_state(chat_id, user_id)
    if user_state.state == ENTER_TIMES:
        if user_state.pill.times.count() != 0:
            user_state.state = CHOOSE_REPEATING
            user_state.save()
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
    user_state = State.get_state(chat_id, user_id)

    # Check if we are waiting for confirmation and the right user answered
    if user_state.state == CHOOSE_REPEATING:
        if text == EVERY_DAY:
            RepeatEveryDay(pill=user_state.pill).save()
            user_state.clean()
            bot.editMessageText(
                text="Finished. Repeating annoucement every day.",
                chat_id=chat_id,
                message_id=query.message.message_id)
        elif text == EVERY_N_DAY:
            user_state.state = ENTER_N_DAYS
            user_state.save()
            bot.editMessageText(text="Please enter number of days:",
                                chat_id=chat_id,
                                message_id=query.message.message_id)
        elif text == WEEK_DAYS:
            user_state.state = ENTER_DATES
            user_state.save()
            reply_markup = gen_reply_week_day_markup(user_state)
            bot.editMessageText(
                text="Choose whcih days you want to be annouced.",
                chat_id=chat_id,
                message_id=query.message.message_id,
                reply_markup=reply_markup)
    elif user_state.state == ENTER_DATES:
        if text == SAVE:
            user_state.clean()
            bot.editMessageText(
                text="Finished.",
                chat_id=chat_id,
                message_id=query.message.message_id)
        else:
            try:
                if int(text[1]):  # create data
                    WeekDaysRepetion(pill=user_state.pill,
                                     day=int(text[0])).save()
                else:
                    WeekDaysRepetion.objects.get(pill=user_state.pill,
                                                 day=int(text[0])).remove()
            except:
                pass
            reply_markup = gen_reply_week_day_markup(user_state)
            bot.editMessageText(
                text="Choose which days you want to be annouced.",
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

    pills = Pill.objects.filter(chat_id=chat_id, user_id=user_id)
    bot.sendMessage(
        chat_id,
        text="List:%s" % (
            "".join(["\n * " + str(i.name) for i in pills]))
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
