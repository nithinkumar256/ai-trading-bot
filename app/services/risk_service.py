import math

# ✅ Config (you can move to .env later)
ACCOUNT_BALANCE = 1000  # USDT (change later)
RISK_PER_TRADE = 0.02   # 2% risk per trade


def calculate_position(symbol_price, stop_loss_price):
    try:
        risk_amount = ACCOUNT_BALANCE * RISK_PER_TRADE
        stop_distance = abs(symbol_price - stop_loss_price)

        if stop_distance <= 0:
            return 0

        quantity = risk_amount / stop_distance

        # fallback for testing
        if quantity <= 0:
            return 1

        return round(quantity, 4)

    except:
        return 1  # safe fallback


def calculate_trade_levels(data):
    try:
        price = float(data.get("close"))
        atr = data.get("atr")

        # ✅ FIX: fallback if ATR missing
        if atr is None or atr == 0:
            atr = price * 0.005  # 0.5% fallback

        atr = float(atr)

        # Stop Loss (ATR based)
        stop_loss = price - (1.5 * atr)

        # Take Profit (RR 1:2)
        take_profit = price + (3 * atr)

        # Safety checks
        if stop_loss <= 0 or take_profit <= 0:
            return None

        return {
            "entry": round(price, 4),
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4)
        }

    except Exception as e:
        print("Risk calc error:", e)
        return None