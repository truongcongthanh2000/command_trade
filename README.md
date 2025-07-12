# Command Trading Bot

A command-line interface (CLI) trading bot for automating trades on cryptocurrency exchanges.


## Features

* **Command-Line Interface:** Control the bot through simple and intuitive commands.
* **Exchange Support:** Binance.
* **Real-time Data:** Fetches live market data to make informed trading decisions.
* **Risk Management:** Set stop-loss and take-profit levels to manage risk.
* **Notifications:** Receive alerts on trades and market conditions.

## Getting Started

- This repo is developed on Python version >= 3.10
- **Clone this repo**:  https://github.com/truongcongthanh2000/command_trade
- Add file config
    - Setup bot telegram and chat_id [how to get chat_id telegram](https://gist.github.com/nafiesl/4ad622f344cd1dc3bb1ecbe468ff9f8a)
    - Create new file config_remote.yaml and fill all fields
- Install all dependencies ```pip3 install -r requirements.txt```
- Run code ```python3 -m command_trade```, you will see all commands in the group/channel chat on telegram.

## Deployment
In this project, I use [Heroku](https://www.heroku.com/) as cloud platform for deployment. Here is the config 
- [Buildpacks](https://devcenter.heroku.com/articles/buildpacks)
    - heroku/python
    - https://github.com/playwright-community/heroku-playwright-buildpack.git
- Region: **Europe** (**Note: Avoid choose USA because lack of support API from binance.us**)
- Stack: **heroku-22** (**Note: Do not use latest version heroku-24 because of incompatible with playwright**)
- Add-ons: **[Fixie](https://elements.heroku.com/addons/fixie)** for forward-proxy to binance APIs.

## Disclaimer

Trading cryptocurrencies involves significant risk. This bot is for educational and informational purposes only and should not be considered financial advice. You are responsible for your own trading decisions. Past performance is not indicative of future results.