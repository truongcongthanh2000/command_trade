import time
from .logger import Logger
from .config import Config
from .notification import Message
from datetime import datetime
import pytz
import json
import apprise
def main():
    config = Config()
    logger = Logger(config, "command_trade_server")
    logger.info(Message(title = f"Start Command Trade - Time: {datetime.fromtimestamp(int(time.time()), tz=pytz.timezone('Asia/Ho_Chi_Minh'))}", body=f"{json.dumps(config.beautify(), indent=2)}", format=apprise.NotifyFormat.TEXT), True)
    while True:
        pass
