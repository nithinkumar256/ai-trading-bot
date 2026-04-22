import requests
import pandas as pd

BASE_URL = "https://api.binance.com"

def get_klines(symbol: str = "BTCUSDT", interval: str = "1m", limit: int = 100):
    url = f"{BASE_URL}/api/v3/klines"
    
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }

    response = requests.get(url, params=params)
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    # Clean data
    df = df[["time", "open", "high", "low", "close", "volume"]]
    
    df["time"] = pd.to_datetime(df["time"], unit='ms')
    df[["open", "high", "low", "close", "volume"]] = df[
        ["open", "high", "low", "close", "volume"]
    ].astype(float)

    return df

def get_current_price(symbols):
    prices = {}

    for symbol in symbols:
        try:
            url = f"{BASE_URL}/api/v3/ticker/price?symbol={symbol}"
            data = requests.get(url).json()

            prices[symbol] = float(data["price"])
        except:
            continue

    return prices