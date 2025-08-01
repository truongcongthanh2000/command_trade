import logging.handlers

from .notification import NotificationHandler
from .config import Config

class Logger:
    Logger = None
    NotificationHandler = None

    def __init__(self, config: Config, logging_service="crypto_trading", enable_notifications=True):
        # Logger setup
        self.Logger = logging.getLogger(logging_service)
        self.Logger.setLevel(logging.DEBUG)
        self.Logger.propagate = False
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        # default is "logs/crypto_trading.log"
        fh = logging.FileHandler(f"logs/{logging_service}.log")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.Logger.addHandler(fh)

        # logging to console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.Logger.addHandler(ch)

        # notification handler
        self.NotificationHandler = NotificationHandler(config, enable_notifications)

    def log(self, message, level="info", notification=True):
        if level == "info":
            self.Logger.info(str(message))
        elif level == "warning":
            self.Logger.warning(str(message))
        elif level == "error":
            self.Logger.error(str(message))
        elif level == "debug":
            self.Logger.debug(str(message))

        if notification and self.NotificationHandler.enabled:
            self.NotificationHandler.send_notification(message)

    def info(self, message, notification=False):
        self.log(message, "info", notification)

    def warning(self, message, notification=False):
        self.log(message, "warning", notification)

    def error(self, message, notification=False):
        self.log(message, "error", notification)

    def debug(self, message, notification=False):
        self.log(message, "debug", notification)
