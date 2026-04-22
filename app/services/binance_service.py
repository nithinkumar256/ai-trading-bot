import requests
import pandas as pd

BASE_URL = "https://testnet.binance.vision"


def get_klines(symbol: str = "BTCUSDT", interval: str = "1m", limit: int = 100):
    url = f"{BASE_URL}/api/v3/klines"

    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }

    response = requests.get(url, params=params)

    # 🔥 safety
    if response.status_code != 200:
        print("❌ Klines API error:", response.text)
        return pd.DataFrame()

    data = response.json()

    if not isinstance(data, list):
        print("❌ Invalid klines response:", data)
        return pd.DataFrame()

    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df = df[["time", "open", "high", "low", "close", "volume"]]

    df["time"] = pd.to_datetime(df["time"], unit='ms')
    df[["open", "high", "low", "close", "volume"]] = df[
        ["open", "high", "low", "close", "volume"]
    ].astype(float)

    return df


# ✅ FIXED PRICE FETCHER
def get_current_price(symbols):
    prices = {}

    for symbol in symbols:
        try:
            url = f"{BASE_URL}/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url)

            if response.status_code != 200:
                print(f"❌ API error {symbol}:", response.text)
                continue

            data = response.json()

            # 🔥 critical validation
            if not isinstance(data, dict) or "price" not in data:
                print(f"❌ Invalid response {symbol}:", data)
                continue

            prices[symbol] = float(data["price"])

        except Exception as e:
            print(f"❌ Price fetch error {symbol}:", e)

    return prices  # ALWAYS dict