import yfinance as yf
from dataclasses import dataclass
from typing import List
import pandas as pd

@dataclass(slots=True)
class StructTicker:
    date: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float

class Ticker:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.data: List[StructTicker] = []

    def load_data(self, period, interval) -> List[StructTicker]:
        self.data.clear()
        df = yf.download(self.ticker, period=period, interval=interval)

        for index, row in df.iterrows():
            self.data.append(
                StructTicker(
                    date=index,
                    open=row["Open"][self.ticker],
                    high=row["High"][self.ticker],
                    low=row["Low"][self.ticker],
                    close=row["Close"][self.ticker],
                    volume=row["Volume"][self.ticker]
                )
            )
        return self.data

    def get_ticker(self) -> str:
        return self.ticker

    def get_data_range(self, start_at_index: int, max: int) -> List[StructTicker]:
        if not self.data:
            return []
        if start_at_index < 0 or start_at_index >= len(self.data):
            raise IndexError("start_at_index is out of bounds")
        if max <= 0:
            raise ValueError("max must be greater than zero")
        end_index = start_at_index + max
        if end_index > len(self.data):
            end_index = len(self.data)
        if end_index < start_at_index:
            raise ValueError("end_index is less than start_at_index")
        return self.data[start_at_index:end_index]

    def get_data(self) -> List[StructTicker]:
        return self.data

    def get_last_data(self) -> StructTicker | None:
        if not self.data:
            return None
        return self.data[-1]

    def __repr__(self):
        return f"Ticker('{self.symbol}')"