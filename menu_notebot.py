#!/usr/bin/python3
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, RegexHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
import re
import yaml


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
def take_note_submenu(bot, update):
    query = update.callback_query
    note_type = parse_category(query.data)
    bot.edit_message_text(chat_id=query.message.chat_id,
                          message_id=query.message.message_id,
                          text=enter_description_message(),
                          reply_markup=enter_description_keyboard())
    # print('{} - {}'.format(note_type, update.message.text))


def review_note_submenu(bot, update):
    pass


def search_note_submenu(bot, update):
    pass


# Keyboards
def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton('Take a new note', callback_data='m1')],
                [InlineKeyboardButton('Review my notes', callback_data='m2')],
                [InlineKeyboardButton('Search all notes', callback_data='m3')],
                [InlineKeyboardButton('Medicine details', callback_data='m4')]]
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
                [InlineKeyboardButton('Edit previous note', callback_data='m2_2')],
                [InlineKeyboardButton('<< Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


def search_notes_menu_keyboard():
    keyboard = [[InlineKeyboardButton('By category', callback_data='m3_1')],
                [InlineKeyboardButton('By note taker', callback_data='m3_2')],
                [InlineKeyboardButton('Last x number of notes', callback_data='m3_3')],
                [InlineKeyboardButton('<< Main menu', callback_data='main')]]
    return InlineKeyboardMarkup(keyboard)


def enter_description_keyboard():
    pass


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


# Helper Functions
def set_note_categories():
    with open('note_categories.txt', 'r') as note_file:
        notes = note_file.read().splitlines()
    return notes


def parse_category(message):
    regex = re.compile(r"take_note_submenu_(.*?)$")
    cat = regex.search(message).group(1)
    return cat


# Main Handlers
def main():
    with open('credentials.yml', 'r') as infile:
        creds = yaml.load(infile)
    updater = Updater("{}".format(creds['api_key']))

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='main'))
    updater.dispatcher.add_handler(CallbackQueryHandler(take_note_menu, pattern='m1'))
    updater.dispatcher.add_handler(CallbackQueryHandler(take_note_submenu, pattern='take_note_submenu_.*?'))
    updater.dispatcher.add_handler(CallbackQueryHandler(review_notes_menu, pattern='m2'))
    updater.dispatcher.add_handler(CallbackQueryHandler(search_notes_menu, pattern='m3'))
    updater.dispatcher.add_handler(CallbackQueryHandler(review_note_submenu, pattern='m2_1'))
    updater.dispatcher.add_handler(CallbackQueryHandler(search_note_submenu, pattern='m3_1'))

    updater.start_polling()


if __name__ == '__main__':
    main()
