import queue
import threading
from os import path

import apprise
import json
from .config import Config

APPRISE_CONFIG_PATH = "config/apprise.yaml"

class Message:
    def __init__(self, body: str, title = 'Command Trade', format = apprise.NotifyFormat.MARKDOWN):
        self.title = title
        self.body = body
        self.format = format
    def __str__(self):
        payload = {
            "title": self.title,
            "body": self.body,
            "format": self.format
        }
        return json.dumps(payload)

class NotificationHandler:
    def __init__(self, cfg: Config, enabled=True):
        if enabled:
            self.apobj = apprise.Apprise()
            if path.exists(APPRISE_CONFIG_PATH):
                config = apprise.AppriseConfig()
                config.add(APPRISE_CONFIG_PATH)
                self.apobj.add(config)
            else:
                self.apobj = apprise.Apprise()
                self.apobj.add(cfg.TELEGRAM_NOTIFY_URL, tag='telegram')
            self.queue = queue.Queue()
            self.start_worker()
            self.enabled = True
        else:
            self.enabled = False

    def start_worker(self):
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        while True:
            # message, attachments = self.queue.get()
            message = self.queue.get()
            self.apobj.notify(body=message.body, title=message.title, body_format=message.format, interpret_escapes=True)

            # if attachments:
            #     self.apobj.notify(body=message.body, attach=attachments)
            # else:
            #     self.apobj.notify(body=message.body)
            self.queue.task_done()

    def send_notification(self, message: Message, attachments=None):
        if self.enabled:
            self.queue.put(message)
            # self.queue.put((message, attachments or []))
