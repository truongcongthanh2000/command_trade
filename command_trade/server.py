import time
from .logger import Logger
from .config import Config
from .notification import Message
from .binance_api import BinanceAPI
from .command import Command
from .threads import Threads
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update

def main():
    config = Config()
    logger = Logger(config, "command_trade_server")
    binanceAPI = BinanceAPI(config, logger)
    threads = Threads(config, logger)
    command = Command(config, logger, binance_api=binanceAPI, threads=threads)
    if config.COMMAND_ENABLED == True:
        application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).read_timeout(7).get_updates_read_timeout(42).post_init(command.post_init).build()
        application.add_handler(CommandHandler("help", command.help))
        application.add_handler(CommandHandler("start", command.start))
        application.add_handler(CommandHandler("info", command.info))
        application.add_handler(CommandHandler("forder", command.forder))
        application.add_handler(CommandHandler("fclose", command.fclose))
        application.add_handler(CommandHandler("fch", command.fchart))
        application.add_handler(CommandHandler("fp", command.fprices))
        application.add_handler(CommandHandler("fstats", command.fstats))
        application.add_handler(CommandHandler("flimit", command.flimit))
        application.add_handler(CommandHandler("ftpsl", command.ftpsl))
        application.add_handler(CommandHandler("falert", command.falert))
        application.add_handler(CommandHandler("falert_track", command.falert_track))
        application.add_handler(CommandHandler("falert_list", command.falert_list))
        application.add_handler(CommandHandler("falert_remove", command.falert_remove))
        application.add_handler(CommandHandler("freplies", command.freplies))
        application.add_handler(CommandHandler("freplies_track", command.freplies_track))
        application.add_handler(CommandHandler("freplies_list", command.freplies_list))
        application.add_handler(CommandHandler("freplies_remove", command.freplies_remove))
        application.add_handler(MessageHandler(~filters.COMMAND, command.info_message))
        application.add_error_handler(command.error)
        application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
    while True:
        pass
