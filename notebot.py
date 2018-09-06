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


def find_vitals(message):
    regex = re.compile(r"vital[s]?", re.IGNORECASE)
    if re.findall(regex, message):
        return True
    else:
        return False


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
    print(url)
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
    last_x_notes_regex = re.compile("/last([\d]+)notes")
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            owner_id = update["message"]["chat"]["id"]
            owner_name = update["message"]["from"]["first_name"]
            datetime = time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(update["message"]["date"]))
        except KeyError:
            text = update["edited_message"]["text"]
            owner_id = update["edited_message"]["chat"]["id"]
            owner_name = update["edited_message"]["from"]["first_name"]
            datetime = time.strftime('%m-%d-%Y %H:%M:%S', time.localtime(update["edited_message"]["date"]))
        items = db.get_items_by_owner_id(owner_id)
        notes = set_note_categories()
        if re.match(last_x_notes_regex, text):
            items = db.get_last_x_requested_items(last_x_notes_regex.search(text).group(1), datetime=True)
            message = ""
            for desc, date in items:
                message += "({}) {}\n".format(date, desc)
            send_message(message, owner_id, url)
        elif text == "/help":
            help_message = "Welcome to dad bot the Hospital Tracker Extraordinaire\n" \
                           "Type /help for this help menu (this list of commands)\n" \
                           "Type /takenote to start a new note\n" \
                           "Type /mynotes to see a list of all notes you have taken\n" \
                           "Type /lastXnotes to see the last X number of notes Ex: 'last5notes'\n"
            send_message(help_message, owner_id, url, reply_markup=None)
        elif text == "/takenote":
            keyboard = build_keyboard(notes)
            send_message("Select a note category", owner_id, url, keyboard)
            # flag = "takenote"
        elif text == "/mynotes":
            items = db.get_items_by_owner_id(owner_id)
            message = "\n".join(items)
            send_message(message, owner_id, url)
        elif text.startswith("/"):
            continue
        elif text in items:
            # refactor for deletes later
            db.delete_item(text, owner_id)
            items = db.get_items_by_owner_id(owner_id)
            keyboard = build_keyboard(items)
            send_message("Select an item to delete", owner_id, url, keyboard)
        elif text in notes:
            send_message("Enter description", owner_id, url)
            note_flag.set_note_value(text)
        else:
            if note_flag.note_value is not None:
                text = "{} - {}".format(note_flag.note_value, text)
                db.add_item(text, owner_id, note_flag.note_value, owner_name, datetime)
                if find_vitals(text):
                    send_message("Enter Vitals Data", owner_id, url)
                    note_flag.set_flag("Vitals")
                note_flag.set_note_value(None)
                send_message(text, "-272948016", url)
            elif note_flag.flag == "Vitals":
                text = "{} - {}".format(note_flag.flag, text)
                db.add_item(text, owner_id, note_flag.note_value, owner_name, datetime)
                note_flag.set_flag(None)
                send_message(text, "-272948016", url)


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
