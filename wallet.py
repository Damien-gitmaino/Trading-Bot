import os
import pickle
from dataclasses import dataclass
from typing import List

import pandas as pd

from ticker import Ticker, StructTicker

from utils.logger import Logger

logger = Logger("Wallet")


@dataclass(slots=True)
class Position:
    date: pd.Timestamp
    entry_price: float
    ticker: Ticker
    amount: float
    stop_loss: float
    take_profit: float


class Wallet:
    def __init__(self, balance, filename: str = None):
        self.balance = balance
        self.positions: List[Position] = []

        if filename and os.path.exists(filename):
            try:
                loaded_wallet = Wallet.load(filename)
                self.balance = loaded_wallet.balance
                self.positions = loaded_wallet.positions
                logger.log(f"Wallet loaded from '{filename}'.")
            except Exception as e:
                logger.log(f"Failed to load wallet from '{filename}': {e}. Starting with a new wallet.")

        self._filename = filename  # Save the filename for use in save()

    def buy(self, ticker, amount, price, stop_loss, take_profit):
        if amount <= 0 or price <= 0:
            raise ValueError("Amount and price must be greater than zero.")

        total_cost = amount * price
        if total_cost > self.balance:
            raise ValueError("Insufficient balance to complete the purchase.")

        self.balance -= total_cost
        position = Position(date=pd.Timestamp.now(), entry_price=price, ticker=ticker, amount=amount,
                            stop_loss=stop_loss, take_profit=take_profit)
        self.positions.append(position)
        logger.log(
            f"Bought {round(amount, 2)} of {ticker.get_ticker()} at {round(price, 2)}, stop loss at {round(stop_loss, 2)}, take profit at {round(take_profit, 2)}")
        self.save('wallet.pkl')
        return position

    def sell(self, ticker, price):
        if price <= 0:
            raise ValueError("Amount and price must be greater than zero.")

        position = next((p for p in self.positions if p.ticker == ticker), None)
        if not position:
            raise ValueError(f"No position found for ticker {ticker} with sufficient amount.")

        total_value = position.amount * price
        self.balance += total_value
        logger.log(
            f"Sold {round(position.amount, 2)} of {ticker.get_ticker()} at {round(price, 2)}, entry price was {round(position.entry_price, 2)}")
        if price > position.entry_price:
            logger.log(
                f'\033[92mProfit made: {round(total_value - (position.amount * position.entry_price), 2)}\033[0m')
        else:
            logger.log(f'\033[91mLoss made: {round(total_value - (position.amount * position.entry_price), 2)}\033[0m')
        position.amount -= position.amount

        if position.amount == 0:
            self.positions.remove(position)

        self.save('wallet.pkl')
        return total_value

    def get_balance(self):
        return self.balance

    def get_positions(self):
        return self.positions

    def get_position(self, ticker):
        for position in self.positions:
            if position.ticker.get_ticker() == ticker:
                return position
        return None

    def save(self, filename: str = None):
        if not filename:
            filename = self._filename
        if not filename:
            raise ValueError("No filename provided to save the wallet.")
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
        logger.log(f"Wallet saved to '{filename}'.")

    @staticmethod
    def load(filename: str) -> 'Wallet':
        with open(filename, 'rb') as f:
            return pickle.load(f)


def check_positions(wallet: Wallet, data: List[StructTicker], ticker: Ticker):
    position = wallet.get_position(ticker.get_ticker())
    if position is None:
        return
    current_price = data[-1].close
    if current_price <= position.stop_loss or current_price >= position.take_profit:
        logger.log(f"\033[94mClosing position for {position.ticker.get_ticker()}\033[0m")
        wallet.sell(ticker=position.ticker, price=current_price)
        logger.log("\033[94m----------------------\033[0m")
