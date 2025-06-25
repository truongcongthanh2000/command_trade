import queue
import threading
from os import path

import json
from .config import Config
import telegramify_markdown
import telebot
from telebot.types import LinkPreviewOptions, InputMediaPhoto, InputFile
from telebot import apihelper
import datetime
import requests
class Message:
    def __init__(self, body: str, chat_id: int = 0, title = 'Command Trade', format: str | None = "MarkdownV2", image: str | None = None, images: list[str] | None = None, group_message_id: int | None = None):
        self.title = title
        self.body = body
        self.format = format
        self.image = image
        self.images = images
        self.chat_id = chat_id
        self.group_message_id = group_message_id
    def __str__(self):
        payload = {
            "title": self.title,
            "body": self.body,
            "format": self.format,
            "image": self.image,
            "images": self.images,
            "chat_id": self.chat_id,
            "group_message_id": self.group_message_id
        }
        return json.dumps(payload)
    def build_text_notify(self):
        return f"**{self.title}**\n{self.body}"

class NotificationHandler:
    def __init__(self, cfg: Config, enabled=True):
        if enabled:
            self.config = cfg
            self.queue = queue.Queue()
            self.start_worker()
            self.enabled = True
            self.telebot = telebot.TeleBot(token=cfg.TELEGRAM_BOT_TOKEN)
        else:
            self.enabled = False


    def notify(self, message: Message):
        text_msg = message.build_text_notify()
        if message.format is not None:
            text_msg = telegramify_markdown.markdownify(text_msg)
        if message.images is not None and len(message.images) > 1:
            list_media = []
            for index, image in enumerate(message.images):
                if index == 0:
                    list_media.append(InputMediaPhoto(
                        media=image,
                        caption=text_msg,
                        parse_mode=message.format
                    ))
                else:
                    list_media.append(InputMediaPhoto(media=image))
            try:
                self.telebot.send_media_group(chat_id = message.chat_id, media=list_media, reply_to_message_id=message.group_message_id)
            except Exception as err:
                self.telebot.send_message(chat_id = message.chat_id, text=text_msg + "\n" + f"Error send media group, err: {err}", parse_mode=message.format, link_preview_options=LinkPreviewOptions(is_disabled=True), reply_to_message_id=message.group_message_id)
        elif message.image is not None and message.image != "":
            try:
                self.telebot.send_photo(chat_id = message.chat_id, photo=message.image, caption = text_msg, parse_mode=message.format, reply_to_message_id=message.group_message_id)
            except Exception as err:
                print(datetime.datetime.now(), " - ERROR - ", Message(
                    title=f"Error Notification.send_photo, image={message.image}",
                    body=f"Error: {err=}", 
                    format=None,
                    chat_id=self.config.TELEGRAM_LOG_PEER_ID
                ))
                request = requests.get(message.image, stream=True)
                with open("photo.png", "wb+") as file:
                    for c in request:
                        file.write(c)
                self.telebot.send_photo(chat_id = message.chat_id, photo=InputFile("photo.png"), caption = text_msg, parse_mode=message.format, reply_to_message_id=message.group_message_id)
        else:
            self.telebot.send_message(chat_id = message.chat_id, text=text_msg, parse_mode=message.format, link_preview_options=LinkPreviewOptions(is_disabled=True), reply_to_message_id=message.group_message_id)

    def start_worker(self):
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        while True:
            # message, attachments = self.queue.get()
            message = self.queue.get()
            self.notify(message)
            self.queue.task_done()

    def send_notification(self, message: Message, attachments=None):
        if self.enabled:
            self.queue.put(message)
            # self.queue.put((message, attachments or []))
