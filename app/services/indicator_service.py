import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volume import VolumeWeightedAveragePrice

def calculate_indicators(df: pd.DataFrame):
    df = df.copy()

    # RSI
    rsi = RSIIndicator(close=df["close"], window=14)
    df["rsi"] = rsi.rsi()

    # EMA
    ema9 = EMAIndicator(close=df["close"], window=9)
    ema21 = EMAIndicator(close=df["close"], window=21)
    df["ema9"] = ema9.ema_indicator()
    df["ema21"] = ema21.ema_indicator()

    # MACD
    macd = MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    # VWAP
    vwap = VolumeWeightedAveragePrice(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        volume=df["volume"]
    )
    df["vwap"] = vwap.volume_weighted_average_price()

    return df