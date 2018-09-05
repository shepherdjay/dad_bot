from dbhelper import DBHelper

import json
import requests
import time
import urllib
import yaml
import re


class NoteEvent:
    flag = None
    note_value = None

    def set_flag(self, new_flag):
        self.flag = new_flag

    def set_note_value(self, new_note_value):
        self.note_value = new_note_value


def parse_category(message):
    regex = re.compile(r"(.*?) - .*?")
    cat = regex.search(message).group(1)
    return cat


def set_note_categories():
    with open('note_categories.txt', 'r') as note_file:
        notes = note_file.read().splitlines()
    return notes


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(url, offset=None):
    """
    Used to poll the JSON file for a given telegram bot
    :param url: The url passed to the bot
    :param offset: Used to identify the most recent updates and account for which ones have been acknowledged
    :return: returns the json of the url call
    """
    # timeout is used to enable "long polling" essentially reducing resource load
    url += "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return text, chat_id


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def send_message(text, chat_id, url, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url += "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


# def echo_all(updates):
#     for update in updates["result"]:
#         try:
#             text = update["message"]["text"]
#             chat = update["message"]["chat"]["id"]
#             send_message(text, chat)
#         except Exception as e:
#             print(e)


def handle_updates(updates, url, note_flag: NoteEvent):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
        except KeyError:
                text = update["edited_message"]["text"]
                chat = update["edited_message"]["chat"]["id"]
        items = db.get_items(chat)
        notes = set_note_categories()
        if text == "/done":
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, url, keyboard)
        elif text == "/help":
            help_message = "Welcome to dad bot the Hospital Tracker Extraordinaire\n" \
                           "Type /help for this message\n" \
                           "Type /takenote to start a new note\n"
            send_message(help_message, chat, url, reply_markup=None)
        elif text == "/takenote":
            keyboard = build_keyboard(notes)
            send_message("Select a note category", chat, url, keyboard)
            # flag = "takenote"
        elif text.startswith("/"):
            continue
        elif text in items:
            db.delete_item(text, chat)
            items = db.get_items(chat)
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", chat, url, keyboard)
        elif text in notes:
            send_message("Enter description", chat, url)
            note_flag.set_note_value(text)
            print(note_flag.note_value)
        else:
            print(note_flag.note_value)
            if note_flag.note_value is not None:
                text = "{} - {}".format(note_flag.note_value, text)
                db.add_item(text, chat, note_flag.note_value)
                items = db.get_items(chat)
                message = "\n".join(items)
                send_message(message, chat, url)
                note_flag.set_note_value(None)
                # flag = None
            # else:
            #     db.add_item(text, chat)
            #     items = db.get_items(chat)
            #     message = "\n".join(items)
            #     send_message(message, chat, url)


def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def main(url):
    db.setup()
    last_update_id = None
    while True:
        updates = get_updates(url, offset=last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates, url, NoteKeeper)
        time.sleep(0.5)


if __name__ == '__main__':
    # test = parse_category("Nurse Visit - Test Description")
    #     # print(test)
    with open('credentials.yml', 'r') as infile:
        creds = yaml.load(infile)
    telegram_api_url = "{}{}/".format(creds['url'], creds['api_key'])
    db = DBHelper()
    NoteKeeper = NoteEvent()
    main(telegram_api_url)