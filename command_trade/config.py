import yaml
import os
import json
import platform
class Config:
    def __init__(self):
        config = {
            "telegram": {
                "bot_token": "",
                "pnl_chat_id": 0,
                "roi_signal": 10,
                "group_chat_id": 10,
                "alert_chat_id": 10,
                "log_peer_id": 10,
                "me": ""
            },
            "command": {
                "api_key": "",
                "api_secret": "",
                "enabled": False,
                "tld": "com"
            },
            "proxies": {
                "nscriptiod_http": "",
                "nscriptiod_https": ""
            },
            "threads": {
                "sla": 600
            }
        }
        if os.path.exists("config/config_remote.yaml"):
            with open("config/config_remote.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
        self.TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or config["telegram"]["bot_token"]
        self.TELEGRAM_PNL_CHAT_ID = int(os.environ.get("TELEGRAM_PNL_CHAT_ID") or config["telegram"]["pnl_chat_id"])
        self.TELEGRAM_ROI_SIGNAL = int(os.environ.get("TELEGRAM_ROI_SIGNAL") or config["telegram"]["roi_signal"])
        self.TELEGRAM_ME = os.environ.get("TELEGRAM_ME") or config["telegram"]["me"]
        self.TELEGRAM_GROUP_CHAT_ID = int(os.environ.get("TELEGRAM_GROUP_CHAT_ID") or config["telegram"]["group_chat_id"])
        self.TELEGRAM_ALERT_CHAT_ID = int(os.environ.get("TELEGRAM_ALERT_CHAT_ID") or config["telegram"]["alert_chat_id"])
        self.TELEGRAM_LOG_PEER_ID = int(os.environ.get("TELEGRAM_LOG_PEER_ID") or config["telegram"]["log_peer_id"])

        self.BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY") or config["binance"]["api_key"]
        self.BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET") or config["binance"]["api_secret"]
        self.BINANCE_TLD = os.environ.get("BINANCE_TLD") or config["binance"]["tld"]

        if "COMMAND_ENABLED" in os.environ:
            self.COMMAND_ENABLED = os.environ.get("COMMAND_ENABLED").lower() == "true"
        else:
            self.COMMAND_ENABLED = config["command"]["enabled"]

        self.PROXIES = {
            "http": os.environ.get("QUOTAGUARDSTATIC_URL") or config["proxies"]["nscriptiod_http"],
            "https": os.environ.get("QUOTAGUARDSTATIC_URL") or config["proxies"]["nscriptiod_https"]
        }

        self.THREADS_SLA = int(os.environ.get("THREADS_SLA") or config["threads"]["sla"])
    def beautify(self):
        response = vars(self).copy()
        response["platform"] = platform.system()
        response["BINANCE_API_KEY"] = "...."
        response["BINANCE_API_SECRET"] = "...."
        return response