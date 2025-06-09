import time
from datetime import datetime, timedelta

import pytz

from config import STARTING_BALANCE, PERIODE, INTERVAL, TICKERS
from strategy import Strategy, calculate_position_amount
from ticker import Ticker
from wallet import Wallet, check_positions

print('Bot started')

print('Setting up the wallet...')
wallet = Wallet(balance=STARTING_BALANCE)
print('Wallet setup complete')

strategy = Strategy()

tickers = [Ticker(ticker) for ticker in TICKERS]

# Define U.S. Market Open and Close Hours (Eastern Time)
MARKET_TIMEZONE = pytz.timezone('US/Eastern')
MARKET_OPEN = datetime.strptime("09:30", "%H:%M").time()
MARKET_CLOSE = datetime.strptime("16:00", "%H:%M").time()

def is_market_open(now_utc):
    now_market = now_utc.astimezone(MARKET_TIMEZONE).time()
    return MARKET_OPEN <= now_market <= MARKET_CLOSE

def seconds_until_next_market_open(now_utc):
    now_market = now_utc.astimezone(MARKET_TIMEZONE)
    next_open = now_market.replace(hour=9, minute=30, second=0, microsecond=0)
    if now_market.time() >= MARKET_CLOSE:
        next_open += timedelta(days=1)
    elif now_market.time() < MARKET_OPEN:
        pass  # today at 9:30
    return (next_open - now_market).total_seconds()

def calculate_delay_to_wait_between_trade():
    interval_seconds = {
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '30m': 1800,
        '1h': 3600,
        '4h': 14400,
        '1d': 86400,
        '1wk': 604800,
        '1mo': 2592000
    }
    return interval_seconds.get(INTERVAL, 60)


while wallet.get_balance() < 2000:
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    if not is_market_open(now_utc):
        wait = seconds_until_next_market_open(now_utc)
        print(f"Market is closed. Waiting {int(wait)} seconds until open...")
        time.sleep(wait)
        continue

    for ticker in tickers:
        ticker.load_data(period=PERIODE, interval=INTERVAL)
        data = ticker.get_data()
        if len(data) < 200:
            continue
        check_positions(wallet, data, ticker)
        catch = strategy.catch_signal(data)

        if catch['signal'] == "BUY" and wallet.get_position(ticker.ticker) is None:
            entry_price = data[-1].close
            amount = calculate_position_amount(wallet, entry_price, risk_percent=0.02)

            if amount > 0:
                wallet.buy(ticker=ticker, amount=amount, price=entry_price, stop_loss=catch['stop_loss'], take_profit=catch['take_profit'])

        elif catch['signal'] == "SELL" and wallet.get_position(ticker.ticker) is not None:
            position = wallet.get_position(ticker.ticker)
            current_price = data[-1].close
            wallet.sell(ticker=ticker, price=current_price)

    delay = calculate_delay_to_wait_between_trade()
    print(f"Sleeping for {delay} seconds...")
    time.sleep(delay)
