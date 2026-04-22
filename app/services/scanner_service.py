import requests
from app.services.binance_service import get_klines
from app.services.indicator_service import calculate_indicators
from app.services.risk_service import calculate_trade_levels, calculate_position
from app.services.paper_trade_service import open_trade, portfolio

BASE_URL = "https://api.binance.com"


# =========================
# GET SYMBOLS
# =========================
def get_top_symbols(limit=30):
    try:
        data = requests.get(f"{BASE_URL}/api/v3/ticker/24hr").json()
    except:
        return []

    valid_pairs = []

    for coin in data:
        symbol = coin.get("symbol")

        if not symbol or not symbol.endswith("USDT"):
            continue

        if any(x in symbol for x in [
            "USDC", "BUSD", "FDUSD", "TUSD", "DAI",
            "USD1", "RLUSD", "USDE", "EUR", "GBP", "UUSDT"
        ]):
            continue

        if not symbol.isascii():
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

    return sorted(valid_pairs, key=lambda x: x["volume"], reverse=True)[:int(limit)]


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

    if rsi is not None:
        if 30 <= rsi <= 45:
            score += 25
        elif 45 < rsi < 60:
            score += 15
        elif rsi > 70:
            score -= 20

    if ema9 and ema21:
        score += 20 if ema9 > ema21 else -10

    if macd and macd_signal:
        score += 20 if macd > macd_signal else -10

    if close and vwap:
        score += 15 if close > vwap else -10

    return score


# =========================
# MAIN SCANNER (FIXED)
# =========================
def scan_market(limit=30):

    # 🚫 DO NOT SCAN if trade already exists
    if portfolio["open_trade"] is not None:
        print("⏸ Trade already open, skipping scan...")
        return []

    symbols_data = get_top_symbols(limit)
    results = []

    for coin in symbols_data:
        symbol = coin["symbol"]
        market_volume = coin["volume"]

        try:
            df_5m = calculate_indicators(get_klines(symbol, "5m"))
            df_15m = calculate_indicators(get_klines(symbol, "15m"))

            latest_5m = df_5m.iloc[-1].to_dict()
            latest_15m = df_15m.iloc[-1].to_dict()

            rsi_5m = latest_5m.get("rsi", 0)
            close_5m = latest_5m.get("close")
            vwap_5m = latest_5m.get("vwap")

            ema9_15m = latest_15m.get("ema9")
            ema21_15m = latest_15m.get("ema21")

            # TREND
            trend = "SIDEWAYS"
            if ema9_15m and ema21_15m:
                if ema9_15m > ema21_15m:
                    trend = "UP"
                elif ema9_15m < ema21_15m:
                    trend = "DOWN"

            score = calculate_score(latest_5m)

            print(symbol, {
                "trend": trend,
                "score": score,
                "rsi": rsi_5m,
                "close": close_5m,
                "vwap": vwap_5m
            })

            decision = "HOLD"

            # =========================
            # BUY SIGNAL
            # =========================
            if (
                trend == "UP" and
                score >= 50 and
                rsi_5m < 60 and
                close_5m and vwap_5m and
                close_5m > vwap_5m
            ):
                decision = "BUY"

                trade_levels = calculate_trade_levels(latest_5m)

                if trade_levels:
                    qty = calculate_position(
                        trade_levels["entry"],
                        trade_levels["stop_loss"]
                    )

                    trade = {
                        "symbol": symbol,
                        "entry": trade_levels["entry"],
                        "stop_loss": trade_levels["stop_loss"],
                        "take_profit": trade_levels["take_profit"],
                        "quantity": qty
                    }

                    print(f"🚀 OPENING TRADE: {symbol}")
                    open_trade(trade)

                    # ✅ STOP scanning after opening trade
                    break

            results.append({
                "symbol": symbol,
                "trend": trend,
                "decision": decision,
                "score": score,
                "rsi_5m": round(rsi_5m, 2),
                "volume_24h": market_volume
            })

        except Exception as e:
            print(f"Error {symbol}: {e}")
            continue

    return sorted(results, key=lambda x: x["score"], reverse=True)


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