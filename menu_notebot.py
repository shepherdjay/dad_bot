#!/usr/bin/python3
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, RegexHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import re
import yaml
import logging
from dbhelper import DBHelper
import time

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Note conversation states
ENTER_DESCRIPTION = range(1)
ENTER_NUMBER = range(1)


def define_take_note_conversation_handler():
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(take_note_submenu, pattern='take_note_submenu_.*?', pass_user_data=True)],
        states={
            ENTER_DESCRIPTION: [MessageHandler(Filters.text, record_take_note_data, pass_user_data=True)],
        },
        fallbacks=[RegexHandler('^Cancel$', cancel, pass_user_data=True)]
    )
    return conv_handler


def define_last_x_note_conversation_handler():
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(last_x_notes_submenu, pattern='last_x_submenu', pass_user_data=True)],
        states={
            ENTER_DESCRIPTION: [MessageHandler(Filters.text, send_last_x_data, pass_user_data=True)],
        },
        fallbacks=[RegexHandler('^Cancel$', cancel, pass_user_data=True)]
    )
    return conv_handler


def record_take_note_data(bot, update, user_data):
    db = DBHelper()
    text = update.message.text
    category = user_data['note_type']
    user_data[category] = text
    db_desc = "{} - {}".format(user_data['note_type'], text)
    message = "{} - {}".format(user_data['note_type'], text)
    update.message.reply_text("Success! Note: {}".format(message))
    bot.send_message(chat_id="-272948016",
                     text=message)
    db.add_item(db_desc, update.message.chat.id, user_data['note_type'], update.message.chat.first_name,
                update.message.date)
    del user_data['note_type']
    time.sleep(.5)
    start(bot, update)

    return ConversationHandler.END


def send_last_x_data(bot, update, user_data):
    db = DBHelper()
    print(update.message.text)
    items = db.get_last_x_requested_items(update.message.text, datetime=True)
    message = ""
    for desc, date in items:
        message += "({}) {}\n".format(date, desc)
    update.message.reply_text(message)
    time.sleep(.5)
    start(bot, update)

    return ConversationHandler.END


def cancel(bot, update, user_data):
    if 'note_type' in user_data:
        del user_data['note_type']

    update.message.reply_text("Note cancelled. Returning to main menu.")
    user_data.clear()

    return ConversationHandler.END


# Bot
def start(bot, update):
    update.message.reply_text(main_menu_message(), reply_markup=main_menu_keyboard())


def main_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=main_menu_message(),
                          reply_markup=main_menu_keyboard())


def take_note_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=take_note_menu_message(),
                          reply_markup=take_note_menu_keyboard())


def review_notes_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=review_notes_menu_message(),
                          reply_markup=review_notes_menu_keyboard())


def search_notes_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=search_notes_menu_message(),
                          reply_markup=search_notes_menu_keyboard())


# sub menus and actions
def take_note_submenu(bot, update, user_data):
    query = update.callback_query
    note_type = parse_category(query.data)
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=enter_description_message(),)
    user_data['note_type'] = note_type
    return ENTER_DESCRIPTION


def my_notes_submenu(bot, update):
    db = DBHelper()
    query = update.callback_query
    message = str()
    for items, datetime in db.get_items_by_owner_id(query.message.chat_id, datetime=True):
        message += "({}) {}\n".format(datetime, items)
    bot.send_message(chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     text=message,)
    time.sleep(1)
    bot.send_message(chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     text=main_menu_message(),
                     reply_markup=main_menu_keyboard())


def last_x_notes_submenu(bot, update, user_data):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=enter_number_of_notes_message(), )
    return ENTER_NUMBER


# Keyboards
def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Take a new note', callback_data='m1')],
                [InlineKeyboardButton('Review my notes', callback_data='m2')],
                [InlineKeyboardButton('Search all notes', callback_data='m3')]]
                # [InlineKeyboardButton('Medicine details', callback_data='m4')]]
    return InlineKeyboardMarkup(keyboard)


def take_note_menu_keyboard():
    note_categories = set_note_categories()
    m_count = 0
    keyboard = []
    while m_count < len(note_categories):
        keyboard.append([InlineKeyboardButton(note_categories[m_count],
                                              callback_data='take_note_submenu_{}'.format(note_categories[m_count])),
                         InlineKeyboardButton(note_categories[m_count + 1],
                                              callback_data='take_note_submenu_{}'.format(
                                                  note_categories[m_count + 1]))])
        m_count += 2
    keyboard.append([InlineKeyboardButton('<< Main menu', callback_data='main')])
    return InlineKeyboardMarkup(keyboard)


def review_notes_menu_keyboard():
    keyboard = [[InlineKeyboardButton('My notes', callback_data='m2_1')],
                # [InlineKeyboardButton('Edit previous note', callback_data='m2_2')],
                [InlineKeyboardButton('<< Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


def search_notes_menu_keyboard():
    keyboard = [# [InlineKeyboardButton('By category', callback_data='m3_1')],
                # [InlineKeyboardButton('By note taker', callback_data='m3_2')],
                [InlineKeyboardButton('Last x number of notes', callback_data='last_x_submenu')],
                [InlineKeyboardButton('<< Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


# Messages
def main_menu_message():
    return 'What would you like dad_bot to do?'


def take_note_menu_message():
    return 'Choose a note category:'


def review_notes_menu_message():
    return 'What do you need to do with your notes?'


def search_notes_menu_message():
    return 'How would you like to search your notes?'


def enter_description_message():
    return 'Enter the note description:'


def enter_number_of_notes_message():
    return 'Enter the number of notes you would like to see:'


# Helper Functions
def set_note_categories():
    with open('note_categories.txt', 'r') as note_file:
        notes = note_file.read().splitlines()
    return notes


def parse_category(message):
    regex = re.compile(r"take_note_submenu_(.*?)$")
    cat = regex.search(message).group(1)
    return cat


def error(bot, update, error):
    print('hit error')
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


# Main Handlers
def main():
    with open('credentials.yml', 'r') as infile:
        creds = yaml.load(infile)
    updater = Updater("{}".format(creds['api_key']))

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
    updater.dispatcher.add_handler(CallbackQueryHandler(take_note_menu, pattern='m1'))
    take_note_conv_handler = define_take_note_conversation_handler()
    updater.dispatcher.add_handler(take_note_conv_handler)
    last_x_notes_conv_handler = define_last_x_note_conversation_handler()
    updater.dispatcher.add_handler(last_x_notes_conv_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(review_notes_menu, pattern='^m2$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(search_notes_menu, pattern='m3'))
    updater.dispatcher.add_handler(CallbackQueryHandler(my_notes_submenu, pattern='^m2_1$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(last_x_notes_submenu, pattern='m3_1'))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()


if __name__ == '__main__':
    main()
