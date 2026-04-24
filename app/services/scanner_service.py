import requests
import time
from app.services.binance_service import get_klines
from app.services.indicator_service import calculate_indicators
from app.services.risk_service import calculate_trade_levels, calculate_position
from app.services.paper_trade_service import open_trade, portfolio

BASE_URL = "https://api.binance.com"

# =========================
# 🔥 GLOBAL STATE (COOLDOWN)
# =========================
last_traded_symbol = None
last_trade_time = 0


# =========================
# GET SYMBOLS
# =========================
def get_top_symbols(limit=30):
    try:
        response = requests.get(f"{BASE_URL}/api/v3/ticker/24hr")

        if response.status_code != 200:
            print("❌ Binance API error:", response.text)
            return []

        data = response.json()

        if not isinstance(data, list):
            return []

    except Exception as e:
        print("❌ Fetch error:", e)
        return []

    valid_pairs = []

    for coin in data:
        symbol = coin.get("symbol")

        if not symbol or not symbol.endswith("USDT"):
            continue

        try:
            volume_24h = float(coin.get("quoteVolume", 0))
        except:
            continue

        if volume_24h < 10_000_000:
            continue

        valid_pairs.append({
            "symbol": symbol,
            "volume": volume_24h
        })

    return sorted(valid_pairs, key=lambda x: x["volume"], reverse=True)[:limit]


# =========================
# SCORING ENGINE
# =========================
def calculate_score(data):
    score = 0

    rsi = data.get("rsi")
    ema9 = data.get("ema9")
    ema21 = data.get("ema21")
    macd = data.get("macd")
    macd_signal = data.get("macd_signal")
    close = data.get("close")
    vwap = data.get("vwap")

    if rsi and 35 <= rsi <= 65:
        score += 20

    if ema9 and ema21 and ema9 > ema21:
        score += 20

    if macd and macd_signal and macd > macd_signal:
        score += 20

    if close and vwap and close > vwap:
        score += 15

    return score


# =========================
# MAIN SCANNER (UPGRADED)
# =========================
def scan_market(limit=30):

    global last_traded_symbol, last_trade_time

    balance = portfolio["balance"]

    if portfolio["open_trade"] is not None:
        print("⏸ Trade already open, skipping scan...")
        return []

    symbols_data = get_top_symbols(limit)

    for coin in symbols_data:
        symbol = coin["symbol"]

        try:
            # ⛔ COOLDOWN (VERY IMPORTANT)
            if symbol == last_traded_symbol and (time.time() - last_trade_time < 120):
                continue

            df_5m = calculate_indicators(get_klines(symbol, "5m"))
            df_15m = calculate_indicators(get_klines(symbol, "15m"))

            latest_5m = df_5m.iloc[-1]
            latest_15m = df_15m.iloc[-1]

            close = latest_5m["close"]

            # 🔥 PRICE FILTER
            if close < 1:
                continue

            vwap = latest_5m["vwap"]
            rsi = latest_5m["rsi"]

            ema9 = latest_15m["ema9"]
            ema21 = latest_15m["ema21"]

            trend = "UP" if ema9 > ema21 else "DOWN"

            score = calculate_score(latest_5m.to_dict())

            # =========================
            # 🔥 STRONG FILTERS
            # =========================

            # Volume spike
            volume = latest_5m["volume"]
            avg_volume = df_5m["volume"].tail(20).mean()
            volume_spike = volume > avg_volume * 1.3

            # ATR filter
            atr = latest_5m["atr"]
            active_market = atr > (0.0005 * close)

            # Breakout
            recent_high = df_5m["high"].tail(20).max()
            breakout = close > recent_high * 0.998

            # 🔥 STRONG CANDLE (UPGRADE)
            candle_body = abs(latest_5m["close"] - latest_5m["open"])
            candle_range = latest_5m["high"] - latest_5m["low"]
            strong_candle = candle_body > (0.6 * candle_range)

            print(symbol, score, volume_spike, active_market, breakout)

            # =========================
            # 🚀 ENTRY LOGIC
            # =========================
            if (
                trend == "UP" and
                score >= 55 and
                rsi < 65 and
                close > vwap and
                strong_candle and
                (volume_spike or breakout) and
                active_market
            ):

                trade_levels = calculate_trade_levels(latest_5m.to_dict())

                if trade_levels:
                    qty = calculate_position(
                        trade_levels["entry"],
                        trade_levels["stop_loss"],
                        balance
                    )

                    trade = {
                        "symbol": symbol,
                        "entry": trade_levels["entry"],
                        "stop_loss": trade_levels["stop_loss"],
                        "take_profit": trade_levels["take_profit"],
                        "quantity": qty,
                        "trailing_level": 0
                    }

                    print(f"🚀 OPENING TRADE: {symbol}")

                    open_trade(trade)

                    # 🔥 SAVE LAST TRADE
                    last_traded_symbol = symbol
                    last_trade_time = time.time()

                    break

        except Exception as e:
            print(f"Error {symbol}: {e}")
            continue

    return []
# =========================
# BEST TRADE
# =========================
def pick_best_trade(scanned_data):
    if not scanned_data:
        return {"message": "No data"}

    buys = [x for x in scanned_data if x["decision"] == "BUY"]

    if buys:
        return sorted(buys, key=lambda x: x["score"], reverse=True)[0]

    return {"message": "No strong trades found"}