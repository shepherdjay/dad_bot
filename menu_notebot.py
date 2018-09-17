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
    send_feed_messages(bot, message)
    db.add_item(db_desc, update.message.chat.id, user_data['note_type'], update.message.chat.first_name,
                update.message.date)
    del user_data['note_type']
    time.sleep(.5)
    start(bot, update)

    return ConversationHandler.END


def send_last_x_data(bot, update, user_data):
    db = DBHelper()
    items = db.get_last_x_requested_items(update.message.text, datetime=True)
    message = ""
    for desc, date in list(items)[::-1]:
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
# menus
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
                          text=generic_note_category_menu_message(),
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


def settings_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=settings_menu_message(),
                          reply_markup=settings_menu_keyboard())


def feed_settings_menu(bot, update):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=generic_question(),
                          reply_markup=note_feed_menu_keyboard())


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
    my_notes = db.get_items_by_owner_id(query.message.chat_id, datetime=True)
    my_notes = list(my_notes)[::-1]
    for items, datetime in my_notes:
        message += "({}) {}\n".format(datetime, items)
    bot.send_message(chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     text=message,)
    time.sleep(1)
    bot.send_message(chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     text=main_menu_message(),
                     reply_markup=main_menu_keyboard())


def cat_search_submenu(bot, update):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=generic_note_category_menu_message(),
                          reply_markup=cat_search_menu_keyboard())


def last_x_notes_submenu(bot, update, user_data):
    query = update.callback_query
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=enter_number_of_notes_message(),)
    return ENTER_NUMBER


# Keyboards
def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Take a new note', callback_data='m1')],
                [InlineKeyboardButton('Review my notes', callback_data='m2')],
                [InlineKeyboardButton('Search all notes', callback_data='m3')],
                # [InlineKeyboardButton('Medicine details', callback_data='m4')],
                [InlineKeyboardButton('Settings', callback_data='settings')]]
    return InlineKeyboardMarkup(keyboard)


def take_note_menu_keyboard():
    note_categories = set_note_categories()
    keyboard = []
    for cat in note_categories:
        keyboard.append(InlineKeyboardButton(cat, callback_data='take_note_submenu_{}'.format(cat)))
    keyboard.append(InlineKeyboardButton('<< Main menu', callback_data='main'))
    return InlineKeyboardMarkup(build_menu(keyboard))


def cat_search_menu_keyboard():
    note_categories = set_note_categories()
    keyboard = []
    for cat in note_categories:
        keyboard.append(InlineKeyboardButton(cat, callback_data='cat_search_{}'.format(cat)))
    keyboard.append(InlineKeyboardButton('<< Main menu', callback_data='main'))
    return InlineKeyboardMarkup(build_menu(keyboard))


def review_notes_menu_keyboard():
    keyboard = [[InlineKeyboardButton('My notes', callback_data='m2_1')],
                # [InlineKeyboardButton('Edit previous note', callback_data='m2_2')],
                [InlineKeyboardButton('<< Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


def search_notes_menu_keyboard():
    keyboard = [[InlineKeyboardButton('By category', callback_data='cat_search')],
                # [InlineKeyboardButton('By note taker', callback_data='m3_2')],
                [InlineKeyboardButton('Last x number of notes', callback_data='last_x_submenu')],
                [InlineKeyboardButton('<< Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


def settings_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Note feed settings', callback_data='note_feed_settings')],
                [InlineKeyboardButton('<< Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


def note_feed_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Activate note feed', callback_data='start_note_feed')],
                [InlineKeyboardButton('Deactivate note feed', callback_data='stop_note_feed')],
                [InlineKeyboardButton('<< Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


# Messages
def main_menu_message():
    return 'What would you like dad_bot to do?'


def generic_note_category_menu_message():
    return 'Choose a note category:'


def review_notes_menu_message():
    return 'What do you need to do with your notes?'


def search_notes_menu_message():
    return 'How would you like to search your notes?'


def enter_description_message():
    return 'Enter the note description:'


def enter_number_of_notes_message():
    return 'Enter the number of notes you would like to see:'


def settings_menu_message():
    return 'What would you like to change?'


def generic_question():
    return 'What would you like to do?'


# menu actions

def activate_feed(bot, update):
    db = DBHelper()
    query = update.callback_query
    if query.message.chat.title:
        db.add_feed_member(query.message.chat_id, query.message.chat.title)
        message = 'Success: Added the group "{}" to note feed!'.format(query.message.chat.title)
    else:
        db.add_feed_member(query.message.chat_id, query.message.chat.first_name)
        message = "Success: {} added to note feed!".format(query.message.chat.first_name)
    bot.send_message(chat_id=query.message.chat_id, text=message, reply_markup=main_menu_keyboard())


def deactivate_feed(bot, update):
    db = DBHelper()
    query = update.callback_query
    if query.message.chat.title:
        db.del_feed_member(query.message.chat_id)
        message = 'Success: Removed the group "{}" from the note feed!'.format(query.message.chat.title)
    else:
        db.del_feed_member(query.message.chat_id)
        message = "Success: {} removed from note feed!".format(query.message.chat.first_name)
    bot.send_message(chat_id=query.message.chat_id, text=message, reply_markup=main_menu_keyboard())


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


def send_feed_messages(bot, message):
    db = DBHelper()
    chats = db.get_feed_chats()
    for chat in chats:
        bot.send_message(chat_id=chat, text=message)


def build_menu(buttons):
    menu = []
    if len(buttons) % 2 == 0:
        b_count = 0
        while b_count < len(buttons):
            menu.append([buttons[b_count], buttons[b_count+1]])
            print(menu)
            b_count += 2
        menu = [buttons]
    if len(buttons) % 2 == 1:
        last_button = [buttons[-1]]
        b_count = 0
        while b_count < len(buttons)-1:
            menu.append([buttons[b_count], buttons[b_count+1]])
            b_count += 2
        menu.append(last_button)
    return menu


# Main Handlers
def main():
    db = DBHelper()
    db.setup()
    db.setup_feed_table()
    with open('credentials.yml', 'r') as infile:
        creds = yaml.load(infile)
    updater = Updater("{}".format(creds['api_key']))

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
    updater.dispatcher.add_handler(CallbackQueryHandler(take_note_menu, pattern='m1'))
    updater.dispatcher.add_handler(CallbackQueryHandler(review_notes_menu, pattern='^m2$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(search_notes_menu, pattern='m3'))
    updater.dispatcher.add_handler(CallbackQueryHandler(settings_menu, pattern='settings'))
    updater.dispatcher.add_handler(CallbackQueryHandler(feed_settings_menu, pattern='note_feed_settings'))
    take_note_conv_handler = define_take_note_conversation_handler()
    updater.dispatcher.add_handler(take_note_conv_handler)
    last_x_notes_conv_handler = define_last_x_note_conversation_handler()
    updater.dispatcher.add_handler(last_x_notes_conv_handler)
    updater.dispatcher.add_handler(CallbackQueryHandler(activate_feed, pattern='start_note_feed'))
    updater.dispatcher.add_handler(CallbackQueryHandler(deactivate_feed, pattern='stop_note_feed'))
    updater.dispatcher.add_handler(CallbackQueryHandler(my_notes_submenu, pattern='^m2_1$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(last_x_notes_submenu, pattern='m3_1'))
    updater.dispatcher.add_handler(CallbackQueryHandler(cat_search_submenu, pattern='cat_search'))
    updater.dispatcher.add_error_handler(error)

    updater.start_polling()


if __name__ == '__main__':
    main()
