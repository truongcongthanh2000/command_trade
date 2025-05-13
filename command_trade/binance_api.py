from .config import Config
from .logger import Logger
import threading
from contextlib import contextmanager
from typing import Dict, Set, Tuple
from .notification import Message
from binance.client import Client

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
            api_key=config.COMMAND_API_KEY,
            api_secret=config.COMMAND_API_SECRET,
            tld=config.COMMAND_TLD
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

    def f_batch_order(self, batch_orders: list[dict]):
        return self.binance_client.futures_place_batch_order(batchOrders=batch_orders)
    
    def f_change_leverage(self, symbol: str, leverage: int):
        return self.binance_client.futures_change_leverage(symbol=symbol, leverage=leverage)

    def f_price(self, symbol: str) -> float:
        return float(self.binance_client.futures_mark_price(symbol=symbol)["markPrice"])
    
    def f_cancel_all_open_orders(self, symbol: str):
        return self.binance_client.futures_cancel_all_open_orders(symbol=symbol)
    
    def f_get_historical_klines(self, symbol: str):
        return self.binance_client.futures_historical_klines(symbol, )