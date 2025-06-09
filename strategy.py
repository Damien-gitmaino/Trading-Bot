import pandas as pd
from config import STOP_LOSS, MAX_RISK_PER_TRADE
from ticker import StructTicker
from typing import List
from wallet import Position, Wallet


def calculate_rsi(data: List[StructTicker], period=14):
    if len(data) < period + 1:
        return None

    changes = [data[i].close - data[i - 1].close for i in range(1, len(data))]
    gains = [max(c, 0) for c in changes[-period:]]
    losses = [-min(c, 0) for c in changes[-period:]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_ema(data: List[float], window):
    if not data or window <= 0:
        return []
    return pd.Series(data).ewm(span=window, adjust=False).mean().tolist()


def calculate_atr(data: List[StructTicker], period=14):
    if len(data) < period + 1:
        return None
    tr_values = []
    for i in range(1, len(data)):
        high = data[i].high
        low = data[i].low
        prev_close = data[i - 1].close
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_values.append(tr)
    return sum(tr_values[-period:]) / period


def calculate_position_amount(wallet: Wallet, entry_price: float, risk_percent: float):
    if entry_price <= 0:
        print("Entry price must be greater than zero")
        return 0
    if risk_percent <= 0 or risk_percent > 1:
        print("Risk percent must be between 0 and 1")
        return 0

    risk_amount = wallet.get_balance() * risk_percent
    if risk_amount <= 0:
        print("Risk amount must be greater than zero.")
        return 0

    if wallet.get_balance() <= 0 or wallet.get_balance() - risk_amount < 0:
        print("Insufficient balance in the wallet.")
        return 0

    position_size = risk_amount / entry_price
    return position_size


class Strategy:
    def __init__(self):
        self.stop_loss_percentage = STOP_LOSS
        self.max_risk_per_trade = MAX_RISK_PER_TRADE
        self.rsi_period = 14
        self.rsi_buy = 40
        self.rsi_sell = 60
        self.ema_fast = 50
        self.ema_slow = 200
        self.atr_period = 14

    def catch_signal(self, data: List[StructTicker]):
        if len(data) < max(self.ema_slow, self.rsi_period, self.atr_period):
            return {"signal": "HOLD"}

        closes = [d.close for d in data]

        ema_fast = calculate_ema(closes, self.ema_fast)
        ema_slow = calculate_ema(closes, self.ema_slow)
        rsi = calculate_rsi(data, self.rsi_period)
        atr = calculate_atr(data, self.atr_period)

        last_price = closes[-1]

        # Long trend condition
        if ema_fast[-1] > ema_slow[-1]:
            if rsi and rsi < self.rsi_buy:
                return {
                    "signal": "BUY",
                    "stop_loss": last_price - 1.5 * atr,
                    "take_profit": last_price + 2.5 * atr
                }

        # Short trend condition
        elif ema_fast[-1] < ema_slow[-1]:
            if rsi and rsi > self.rsi_sell:
                return {
                    "signal": "SELL",
                    "stop_loss": last_price + 1.5 * atr,
                    "take_profit": last_price - 2.5 * atr
                }

        return {"signal": "HOLD"}

