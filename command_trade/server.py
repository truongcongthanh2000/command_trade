import time
from .logger import Logger
from .config import Config
from .notification import Message
from .binance_api import BinanceAPI
from .command import Command
from datetime import datetime
import pytz
import json
import apprise
from telegram.ext import Application, CommandHandler

def main():
    config = Config()
    logger = Logger(config, "command_trade_server")
    logger.info(Message(title = f"Start Command Trade - Time: {datetime.fromtimestamp(int(time.time()), tz=pytz.timezone('Asia/Ho_Chi_Minh'))}", body=f"{json.dumps(config.beautify(), indent=2)}", format=apprise.NotifyFormat.TEXT), True)

    binanceAPI = BinanceAPI(config, logger)
    command = Command(config, logger, binance_api=binanceAPI)
    if config.COMMAND_ENABLED == True:
        application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).read_timeout(7).get_updates_read_timeout(42).build()
        application.add_handler(CommandHandler("help", command.help))
        application.add_handler(CommandHandler("start", command.start))
        application.add_handler(CommandHandler("info", command.info))
        application.add_handler(CommandHandler("forder", command.forder))
        application.add_handler(CommandHandler("fclose", command.fclose))
        application.add_handler(CommandHandler("fch", command.fchart))
        application.add_handler(CommandHandler("fp", command.fprices))
        application.add_error_handler(command.error)
        application.run_polling()
    while True:
        pass
