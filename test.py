from config import STARTING_BALANCE, PERIODE, INTERVAL, TICKERS
from strategy import Strategy, calculate_position_amount
from ticker import Ticker
from wallet import Wallet, check_positions

print('Bot started')

print('Setting up the wallet...')
wallet = Wallet(balance=STARTING_BALANCE)
print('Wallet setup complete')

strategy = Strategy()

tickers = []

for ticker in TICKERS:
    tickers.append(Ticker(ticker))

for ticker in tickers:
    ticker.load_data(period=PERIODE, interval=INTERVAL)

loop = 0

while loop + 200 < len(tickers[0].get_data()):
    for ticker in tickers:
        data = ticker.get_data_range(start_at_index=loop, max=200)
        if len(data) < 200:
            continue
        check_positions(wallet, data, ticker)
        catch = strategy.catch_signal(data)

        if catch['signal'] == "BUY" and wallet.get_position(ticker.ticker) is None:
            entry_price = data[-1].close
            amount = calculate_position_amount(wallet, entry_price, risk_percent=0.03)

            if amount > 0:
                wallet.buy(ticker=ticker, amount=amount, price=entry_price, stop_loss=catch['stop_loss'], take_profit=catch['take_profit'])

        elif catch['signal'] == "SELL" and wallet.get_position(ticker.ticker) is not None:
            position = wallet.get_position(ticker.ticker)
            current_price = data[-1].close
            wallet.sell(ticker=ticker, price=current_price)

    if wallet.get_balance() > 2000:
        break

    loop += 1

print()
print(f'Backtest complete: {wallet.get_balance()} remaining in the wallet')
print('Positions held:')
for position in wallet.get_positions():
    print(f"{position.ticker.get_ticker()} - Amount: {round(position.amount, 2)}, Entry Price: {round(position.entry_price, 2)}, Date: {position.date}")
