from .config import Config
from .logger import Logger
from .util import convert_to_seconds
import threading
from contextlib import contextmanager
from typing import Dict, Set, Tuple
from .notification import Message
from binance.client import Client
import time

BINANCE_INTERVAL = ["1s", "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]

class BinanceCache:  # pylint: disable=too-few-public-methods
    _balances: Dict[str, float] = {}
    _balances_mutex: threading.Lock = threading.Lock()

    @contextmanager
    def open_balances(self):
        with self._balances_mutex:
            yield self._balances
class BinanceAPI:
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.binance_client = Client(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_API_SECRET,
            tld=config.BINANCE_TLD,
            requests_params={"proxies" : config.PROXIES}
        )

    # spot api
    def get_account(self):
        """
        Get account information
        """
        return self.binance_client.get_account(omitZeroBalances="true")
    
    def get_ticker_price(self, symbol: str):
        price = self.binance_client.get_symbol_ticker(symbol=symbol)
        if price is None or "price" not in price:
            return 0.0
        return float(price["price"])

    # future api
    def get_futures_account(self):
        return self.binance_client.futures_account()
    
    def get_position_info(self, symbol: str | None = None): # include leverage, marginType
        if symbol is None:
            return self.binance_client.futures_position_information(version=2)
        return self.binance_client.futures_position_information(symbol=symbol, version=2)

    def get_current_position(self, symbol: str | None = None):
        if symbol is None:
            return self.binance_client.futures_position_information()
        return self.binance_client.futures_position_information(symbol=symbol)
    
    def f_get_symbol_info(self, symbol: str):
        info = self.f_exchange_info()
        for x in info['symbols']:
            if x['symbol'] == symbol:
                return x
        return None
            
    def f_exchange_info(self):
        return self.binance_client.futures_exchange_info()

    def f_order(self, order: dict):
        return self.binance_client.futures_create_order(side=order["side"], type=order["type"], symbol=order["symbol"], quantity=order["quantity"], timeInForce=order["timeInForce"], price=order["price"])

    def f_batch_order(self, batch_orders: list[dict]):
        return self.binance_client.futures_place_batch_order(batchOrders=batch_orders)
    
    def f_change_margin_type(self, symbol: str, marginType: str = "CROSSED"):
        self.binance_client.futures_change_margin_type(symbol=symbol, marginType=marginType)

    def f_change_leverage(self, symbol: str, leverage: int):
        return self.binance_client.futures_change_leverage(symbol=symbol, leverage=leverage)

    def f_price(self, symbol: str) -> float:
        return float(self.binance_client.futures_symbol_ticker(symbol=symbol)["price"])
    
    def f_cancel_all_open_orders(self, symbol: str):
        return self.binance_client.futures_cancel_all_open_orders(symbol=symbol)
    
    def f_get_historical_klines(self, symbol: str, interval: str | None = None, range: str | None = None):
        if interval is None or interval not in BINANCE_INTERVAL:
            interval = "15m"
        if range is None:
            range = convert_to_seconds(interval) * 21
        else:
            range = convert_to_seconds(range)
        return self.binance_client.futures_historical_klines(symbol, interval, round(time.time() - range) * 1000), interval

    def f_24hr_ticker(self, symbol: str):
        return self.binance_client.futures_ticker(symbol=symbol)
    
    def f_user_trades(self, symbol: str, orderId: int):
        return self.binance_client.futures_account_trades(symbol=symbol, orderId=orderId)