from .logger import Logger
from .config import Config
from .notification import Message
from .util import remove_job_if_exists
from telegram import Update, LinkPreviewOptions, MessageEntity
import telegramify_markdown
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, Application
import requests
from .binance_api import BinanceAPI
import json
import traceback
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
from datetime import datetime
import time
import pytz

EPS = 1e-2
class Command:
    def __init__(self, config: Config, logger: Logger, binance_api: BinanceAPI):
        self.config = config
        self.logger = logger
        self.binance_api = binance_api

    async def post_init(self, application: Application):
        self.logger.info("Start server")
        await application.bot.set_my_commands([
            ('help', 'Get all commands'),
            ('start', 'Get public, local IP of the server'),
            ('info', 'Get current trade, balance and pnl'),
            ('forder', 'forder buy/sell coin leverage margin sl(opt) tp(opt)'),
            ('fclose', 'fclose coin'),
            ('fch', "Get chart 'fch coin interval(opt, df=15m) range(opt, df=21 * interval)'"),
            ('fp', "Get prices 'fp coin1 coin2 ....'"),
            ('fstats', "Schedule get stats 'fstats interval(seconds)'"),
        ])
        try:
            commands = await application.bot.get_my_commands()
            public_ip = requests.get('https://api.ipify.org', proxies=self.config.PROXIES).text
            msg = f"👋 **Start Command Trade - Time: {datetime.fromtimestamp(int(time.time()), tz=pytz.timezone('Asia/Ho_Chi_Minh'))}**\n"
            msg += f"**Your server public IP is `{public_ip}`, here is list commands:**\n"
            for command in commands:
                msg += f"/{command.command} - {command.description}\n"
            msg += json.dumps(self.config.beautify(), indent=2)
            await application.bot.send_message(self.config.TELEGRAM_GROUP_CHAT_ID, text=telegramify_markdown.markdownify(msg), parse_mode=ParseMode.MARKDOWN_V2, link_preview_options=LinkPreviewOptions(is_disabled=True))
        except Exception as err:
            self.logger.error(Message(
                title=f"Error post_init",
                body=f"Error: {err=}", 
            ), True)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = "/start - Get public, local IP of the server\n"
        msg += "/info - Get current trade, balance and pnl\n"
        msg += "/forder - Make futures market order 'forder buy/sell coin leverage margin sl(optional) tp(optional)'\n"
        msg += "/fclose - Close all position and open order 'fclose coin'\n"
        msg += "/fch - Get chart 'fch coin interval(optional, default=15m) range(optional, default=21 * interval)'\n"
        msg += "/fp - Get prices 'fp coin1 coin2 ....'\n"
        msg += "/fstats - Schedule get stats for current positions 'fstats interval(seconds)'"
        """Handles command /help from the admin"""
        try:
            await update.message.reply_text(text=telegramify_markdown.markdownify(msg), parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as err:
            self.logger.error(Message(
                title=f"Error Command.help - {update}",
                body=f"Error: {err=}", 
            ), True)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles command /start from the admin"""
        try:
            public_ip = requests.get('https://api.ipify.org', proxies=self.config.PROXIES).text
            await update.message.reply_markdown(text=f"👋 Hello, your server public IP is `{public_ip}`\nCommand `/fstats` interval(seconds) to schedule get stats for current positions")
        except Exception as err:
            self.logger.error(Message(
                title=f"Error Command.start - {update}",
                body=f"Error: {err=}", 
            ), True)
    
    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE): # info current spot/future account, ex: balance, pnl, orders, ...
        try:
            msg = self.info_spot() + '\n--------------------\n' + self.info_future()[0]
            msg = telegramify_markdown.markdownify(msg)
            await update.message.reply_text(text=msg, parse_mode=ParseMode.MARKDOWN_V2, link_preview_options=LinkPreviewOptions(is_disabled=True))
        except Exception as err:
            self.logger.error(Message(
                title=f"Error Command.faccount - {update}",
                body=f"Error: {err=}", 
            ), True)
    
    # forder buy/sell coin leverage margin sl(optional) tp(optional)
    async def forder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        side = context.args[0]
        coin = context.args[1].upper()
        leverage = int(context.args[2])
        margin = float(context.args[3])
        try:
            symbol = coin + "USDT"
            # try to change leverage and margin_type for symbol first
            self.f_set_leverage_and_margin_type(symbol, leverage)
            batch_orders = self.f_get_orders(side, symbol, leverage, margin, context)
            self.logger.info(Message(f"👋 Your order for {symbol} is {json.dumps(batch_orders)}"))
            responses = self.binance_api.f_batch_order(batch_orders)
            ok = True
            for idx in range(len(responses)):
                if "code" in responses[idx] and int(responses[idx]["code"]) < 0:
                    # Error
                    self.logger.error(Message(
                        title=f"Error Command.forder - {batch_orders[idx]['side']} - {batch_orders[idx]['type']} - {symbol}",
                        body=f"Error: {responses[idx]['msg']}",
                    ), True)
                    ok = False
            if ok:
                await update.message.reply_text(text=f"👋 Your order for {symbol} is successful\n {json.dumps(batch_orders, indent=2)}")
        except Exception as err:
            self.logger.error(Message(
                title=f"Error Command.forder - {side} - {symbol} - {leverage} - {margin}",
                body=f"Error: {err=}", 
            ), True)
    
    # fclose coin
    async def fclose(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        coin = context.args[0].upper()
        try:
            symbol = coin + "USDT"
            batch_orders = self.f_get_close_positions(symbol)
            self.logger.info(Message(f"👋 Your close positions for {symbol} is {json.dumps(batch_orders)}"))
            responses = self.binance_api.f_batch_order(batch_orders)
            ok = True
            for idx in range(len(responses)):
                if "code" in responses[idx] and int(responses[idx]["code"]) < 0:
                    # Error
                    self.logger.error(Message(
                        title=f"Error Command.forder - {batch_orders[idx]['side']} - {batch_orders[idx]['type']} - {symbol}",
                        body=f"Error: {responses[idx]['msg']}",
                    ), True)
                    ok = False
            if ok:
                cancel_open_orders_response = self.binance_api.f_cancel_all_open_orders(symbol)
                msg = f"👋 Cancel all open orders for {symbol}\n {json.dumps(cancel_open_orders_response, indent=2)}\n-------------\n"
                for idx in range(len(batch_orders)):
                    orderId = int(responses[idx]["orderId"])
                    userTrades = self.binance_api.f_user_trades(symbol, orderId)
                    totalPnl = 0.0
                    for trade in userTrades:
                        totalPnl += float(trade["realizedPnl"])
                        # should need minus commission?
                    batch_orders[idx]["result_trade"] = {
                        "order_id": orderId,
                        "pnl": f"${round(totalPnl, 2)}"
                    }
                msg += f"👋 Your close positions for {symbol} is successful\n {json.dumps(batch_orders, indent=2)}"
                await update.message.reply_text(text=msg)
        except Exception as err:
            self.logger.error(Message(
                title=f"Error Command.fclose - {symbol}",
                body=f"Error: {err=}", 
            ), True)

    # fch coin interval(optional, default=15m) range(optional, default=21 * interval)
    async def fchart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        coin = context.args[0].upper()
        interval = context.args[1] if len(context.args) > 1 else None
        range = context.args[2] if len(context.args) > 2 else None
        try:
            symbol = coin + "USDT"
            data, interval = self.binance_api.f_get_historical_klines(symbol, interval, range)
            ticker_24h = self.binance_api.f_24hr_ticker(symbol)
            buffer = self.generate_chart("FUTURES", symbol, data, interval)
            caption_msg = self.build_caption(f"https://www.binance.com/en/futures/{symbol}", symbol, ticker_24h)
            await update.message.reply_photo(photo=buffer, caption=telegramify_markdown.markdownify(caption_msg), parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as err:
            self.logger.error(Message(
                title=f"Error Command.fchart - {symbol}",
                body=f"Error: {err=}", 
            ), True)

    # fp coin1 coin2 ....
    async def fprices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            caption_msg = ''
            for coin in context.args:
                symbol = coin.upper() + "USDT"
                ticker_24h = self.binance_api.f_24hr_ticker(symbol)
                if len(caption_msg) > 0:
                    caption_msg += '---------------------\n'
                caption_msg = caption_msg + self.build_caption(f"https://www.binance.com/en/futures/{symbol}", symbol, ticker_24h)
            await update.message.reply_text(text=telegramify_markdown.markdownify(caption_msg), parse_mode=ParseMode.MARKDOWN_V2, link_preview_options=LinkPreviewOptions(is_disabled=True))
        except Exception as err:
            self.logger.error(Message(
                title=f"Error Command.fprice - {symbol}",
                body=f"Error: {err=}", 
            ), True)

    # fstats interval(seconds)
    async def fstats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        interval = int(context.args[0])
        try:
            self.f_stats(interval, context)
            await update.message.reply_text(f"Set stats successful!, interval={interval}s")
        except Exception as err:
            self.logger.error(Message(
                title=f"Error Command.fstats - {interval}",
                body=f"Error: {err=}", 
            ), True)

    async def f_get_stats(self, context: ContextTypes.DEFAULT_TYPE):
        info, totalROI, pnl = self.info_future(True)
        if info == "":
            return
        msg = ""
        if abs(totalROI) >= self.config.TELEGRAM_ROI_SIGNAL: # notify me when signal totalROI >= 10%
            msg += f"{self.config.TELEGRAM_ME} - **${pnl}**\n"
        msg += f"**{datetime.fromtimestamp(int(time.time()), tz=pytz.timezone('Asia/Ho_Chi_Minh'))}** - " + info
        await context.bot.send_message(self.config.TELEGRAM_PNL_CHAT_ID, text=telegramify_markdown.markdownify(msg), parse_mode=ParseMode.MARKDOWN_V2, link_preview_options=LinkPreviewOptions(is_disabled=True))
    
    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log the error and send a telegram message to notify the developer."""
        # traceback.format_exception returns the usual python message about an exception, but as a
        # list of strings rather than a single string, so we have to join them together.
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = "".join(tb_list)
        self.logger.error(Message(f"Exception while handling an update:, exc_info={tb_string}"))

        self.logger.error(Message(
            title=f"Error Command.Update {update}",
            body=f"Error Msg: {context.error}",
        ), True)

    def info_spot(self):
        account_info = self.binance_api.get_account()
        total_balance = 0.0
        info = "**SPOT Account**\n"
        for balance in account_info["balances"]:
            coin = balance["asset"]
            free_price = float(balance["free"])
            locked_price = float(balance["locked"])
            if free_price + locked_price <= EPS:
                continue
            total_balance += free_price + locked_price
            message = ""
            if coin == "USDT":
                message = "USDT: $%.2f" % round(free_price + locked_price, 2)
            else:
                message = f"[{coin}](https://www.binance.com/en/trade/{coin}_USDT?type=spot): ${free_price + locked_price:.2f}"
            message += "\n"
            info += message
        info += "\n"
        info += f"**Total balance**: {total_balance:.2f}"
        return info
    
    def info_future(self, skip_info_when_no_positions: bool = False):
        info = "**Future Account**\n"
        account_info = self.binance_api.get_futures_account()
        positions = self.binance_api.get_current_position()
        if skip_info_when_no_positions == True and len(positions) == 0:
            return ("", 0, 0)
        for position in positions:
            symbol = str(position["symbol"])
            url = f"https://www.binance.com/en/futures/{symbol}"
            amount = float(position["positionAmt"])
            if abs(amount) <= EPS: # Open orders
                continue
            if amount > 0:
                position_type = "**BUY**"
            else:
                position_type = "**SHORT**"
            info_position = f"[{symbol}]({url}): {position_type} **{abs(round(float(position['notional']) / float(position['positionInitialMargin'])))}x**, margin: **${position['positionInitialMargin']}**\n"
            info_position += f"- entryPrice: **${position['entryPrice']}**, marketPrice: **${position['markPrice']}**\n"
            info_position += f"- PNL: **${float(position['unRealizedProfit']):.2f}**, ROI: **{round(float(position['unRealizedProfit']) / float(position['positionInitialMargin']) * 100.0, 2)}%**"
            if float(position['openOrderInitialMargin']) > EPS:
                info_position += f", openMargin: **${position['openOrderInitialMargin']}**\n"
            else:
                info_position += "\n"
            info_position += f"- Close position: `/fclose {symbol.removesuffix('USDT')}`\n\n"
            info += info_position

        info += "\n"
        info += f"**Before Total Balance**: **${float(account_info['totalWalletBalance']):.2f}**\n"
        info += f"**Total Initial Margin**: **${float(account_info['totalInitialMargin']):.2f}** (Position: **${float(account_info['totalPositionInitialMargin']):.2f}**, Open: **${float(account_info['totalOpenOrderInitialMargin']):.2f}**)\n"
        info += f"**Available Balance**: **${float(account_info['availableBalance']):.2f}**\n\n"
        info += f"**Total Unrealized Profit**: **${float(account_info['totalUnrealizedProfit']):.2f}**\n"
        info += f"**Total ROI**: **{round(float(account_info['totalUnrealizedProfit']) / float(account_info['totalWalletBalance']) * 100, 2)}%**\n"
        info += f"**After Total Balance**: **${float(account_info['totalMarginBalance']):.2f}**"
        return (info, round(float(account_info['totalUnrealizedProfit']) / float(account_info['totalWalletBalance']) * 100, 2), round(float(account_info['totalUnrealizedProfit']), 2))
    
    def f_get_orders(self, side: str, symbol: str, leverage: int, margin: float, context: ContextTypes.DEFAULT_TYPE):
        price = self.binance_api.f_price(symbol)
        pair_info = self.binance_api.f_get_symbol_info(symbol)
        quantity_precision = int(pair_info['quantityPrecision']) if pair_info else 3
        quantity = round(margin * leverage / price, quantity_precision)
        if 'b' in side:
            side_upper = "BUY"
        else:
            side_upper = "SELL"
        order = {
            "type": "MARKET",
            "side": side_upper,
            "symbol": symbol,
            "quantity": str(quantity)
        }
        batch_orders = [order]
        if len(context.args) > 4:
            sl_order = {
                "type": "STOP_MARKET",
                "side": "BUY" if side_upper == "SELL" else "SELL",
                "symbol": symbol,
                "stopPrice": context.args[4],
                "closePosition": "true"
            }
            batch_orders.append(sl_order)
        if len(context.args) > 5:
            tp_order = {
                "type": "TAKE_PROFIT_MARKET",
                "side": "BUY" if side_upper == "SELL" else "SELL",
                "symbol": symbol,
                "stopPrice": context.args[5],
                "closePosition": "true"
            }
            batch_orders.append(tp_order)
        return batch_orders

    def f_get_close_positions(self, symbol: str):
        positions = self.binance_api.get_current_position(symbol=symbol)
        batch_orders = []
        for position in positions:
            amount = float(position["positionAmt"])
            if amount > 0:
                side_upper = "BUY"
            else:
                side_upper = "SELL"
            close_order = {
                "type": "MARKET",
                "side": "BUY" if side_upper == "SELL" else "SELL",
                "symbol": symbol,
                "quantity": str(position["positionAmt"]).removeprefix('-'),
            }
            batch_orders.append(close_order)
        return batch_orders

    def generate_chart(self, type: str, symbol: str, data: list, interval: str):
        for line in data:
            del line[6:]
            for i in range(1, len(line)):
                line[i] = float(line[i])
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True).map(lambda x: x.tz_convert('Asia/Ho_Chi_Minh'))
        df.set_index('date', inplace=True)
        # Plotting
        # Create my own `marketcolors` style:
        mc = mpf.make_marketcolors(up='#2fc71e',down='#ed2f1a',inherit=True)
        # Create my own `MatPlotFinance` style:
        s  = mpf.make_mpf_style(base_mpl_style=['bmh', 'dark_background'], marketcolors=mc, y_on_right=True)    
        # Plot it
        buffer = io.BytesIO()
        fig, axlist = mpf.plot(df, figratio=(10, 6), type="candle", tight_layout=True, ylabel = "Precio ($)", returnfig=True, volume=True, style=s)
        # Add Title
        axlist[0].set_title(f"{type} - {symbol} - {interval}", fontsize=25, style='italic')
        fig.savefig(fname=buffer, dpi=300, bbox_inches="tight")
        buffer.seek(0)
        return buffer
    
    def build_caption(self, url: str, symbol: str, ticker_24h: dict):
        pair_info = self.binance_api.f_get_symbol_info(symbol)
        price_precision = int(pair_info['pricePrecision']) if pair_info else 4
        caption_msg = f"#{symbol}: [Link chart]({url})\n"
        caption_msg += f"⚡ {'Price': <8} **{round(float(ticker_24h['lastPrice']), price_precision)}**\n"
        caption_msg += f"🕢 {'24h': <8}**{ticker_24h['priceChangePercent']}%**\n"
        caption_msg += f"📝 {'OPrice': <8}**{round(float(ticker_24h['openPrice']), price_precision)}**\n"
        caption_msg += f"⬆️ {'High': <8}**{round(float(ticker_24h['highPrice']), price_precision)} ({round((float(ticker_24h['highPrice']) - float(ticker_24h['openPrice'])) / float(ticker_24h['openPrice']) * 100, 2)}%**)\n"
        caption_msg += f"⬇️ {'Low': <8}**{round(float(ticker_24h['lowPrice']), price_precision)} ({round((float(ticker_24h['lowPrice']) - float(ticker_24h['openPrice'])) / float(ticker_24h['openPrice']) * 100, 2)}%**)\n"
        return caption_msg
    
    def f_stats(self, interval: int, context: ContextTypes.DEFAULT_TYPE):
        chat_id = self.config.TELEGRAM_PNL_CHAT_ID
        remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(self.f_get_stats, interval=interval, first=0)

    def f_set_leverage_and_margin_type(self, symbol: str, leverage: int = 10, margin_type: str = 'CROSSED'):
        position_info = self.binance_api.get_position_info(symbol)[0]
        if int(position_info["leverage"]) != leverage:
            self.binance_api.f_change_leverage(symbol, leverage)
        if (position_info["marginType"] == "cross" and margin_type != "CROSSED") or (position_info["marginType"] == "isolated" and margin_type != "ISOLATED"):
            self.binance_api.f_change_margin_type(symbol, margin_type)