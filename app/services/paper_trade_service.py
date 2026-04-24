from app.services.binance_service import get_current_price
from app.services.telegram_service import send_telegram

portfolio = {
    "balance": 1000,
    "open_trade": None,
    "history": []
}


# =========================
# OPEN TRADE
# =========================
def open_trade(trade):

    if "symbol" not in trade:
        return {"error": "symbol missing"}

    if portfolio["open_trade"] is not None:
        return {"message": "Trade already open"}

    # 🔥 Ensure trailing level exists
    trade["trailing_level"] = 0

    portfolio["open_trade"] = trade

    msg = (
        f"🚀 NEW TRADE OPENED\n\n"
        f"Symbol: {trade['symbol']}\n"
        f"Entry: {trade['entry']}\n"
        f"SL: {trade['stop_loss']}\n"
        f"TP: {trade['take_profit']}\n"
        f"Qty: {trade['quantity']}"
    )

    send_telegram(msg)
    print(f"✅ OPENED TRADE: {trade['symbol']}")

    return {"message": "Trade opened", "trade": trade}


# =========================
# UPDATE TRADES
# =========================
def update_trades(latest_prices):

    if not isinstance(latest_prices, dict):
        return {"error": "Invalid price data"}

    trade = portfolio.get("open_trade")

    if not trade:
        return {"message": "No open trade"}

    symbol = trade["symbol"]
    price = latest_prices.get(symbol)

    if price is None:
        return {"message": f"No price for {symbol}"}

    entry = trade["entry"]
    tp = trade["take_profit"]
    qty = trade["quantity"]

    profit = (price - entry) * qty

    # =========================
    # 🔥 ADVANCED TRAILING STOP (FIXED)
    # =========================
    level = trade.get("trailing_level", 0)

    # 🔥 EARLIER PROTECTION (CRITICAL FIX)
    if profit > 1.5 and level < 1:
        trade["stop_loss"] = entry
        trade["trailing_level"] = 1
        send_telegram(f"🔒 SL moved to ENTRY ({symbol})")

    elif profit > 3 and level < 2:
        trade["stop_loss"] = entry + (2 / qty)
        trade["trailing_level"] = 2
        send_telegram(f"🔒 Locked +2 profit ({symbol})")

    elif profit > 5 and level < 3:
        trade["stop_loss"] = entry + (4 / qty)
        trade["trailing_level"] = 3
        send_telegram(f"🔒 Locked +4 profit ({symbol})")

    elif profit > 8 and level < 4:
        trade["stop_loss"] = entry + (7 / qty)
        trade["trailing_level"] = 4
        send_telegram(f"🔒 Locked +7 profit ({symbol})")

    elif profit > 12 and level < 5:
        trade["stop_loss"] = entry + (10 / qty)
        trade["trailing_level"] = 5
        send_telegram(f"🔒 Locked +10 profit ({symbol})")

    # =========================
    # TAKE PROFIT
    # =========================
    if price >= tp:
        pnl = (tp - entry) * qty
        portfolio["balance"] += pnl

        send_telegram(
            f"✅ TRADE WON\n{symbol}\n"
            f"Profit: {round(pnl,2)}\n"
            f"Balance: {round(portfolio['balance'],2)}"
        )

        portfolio["history"].append({
            "symbol": symbol,
            "result": "WIN",
            "profit": round(pnl, 2)
        })

        portfolio["open_trade"] = None
        return {"result": "WIN", "pnl": round(pnl, 2)}

    # =========================
    # STOP LOSS / TRAILING EXIT (CRITICAL FIX)
    # =========================
    elif price <= trade["stop_loss"]:

        # 🔥 FORCE EXIT AT SL PRICE (NOT MARKET PRICE)
        exit_price = trade["stop_loss"]

        pnl = (exit_price - entry) * qty
        portfolio["balance"] += pnl

        result_type = "WIN" if pnl > 0 else "LOSS"

        send_telegram(
            f"{'✅' if pnl > 0 else '❌'} TRADE CLOSED\n"
            f"{symbol}\n"
            f"PnL: {round(pnl,2)}\n"
            f"Balance: {round(portfolio['balance'],2)}"
        )

        portfolio["history"].append({
            "symbol": symbol,
            "result": result_type,
            "profit": round(pnl, 2)
        })

        portfolio["open_trade"] = None
        return {"result": "CLOSED", "pnl": round(pnl, 2)}

    return {
        "message": "Trade still open",
        "current_price": price,
        "pnl": round(profit, 2)
    }


# =========================
# PORTFOLIO (LIVE PnL)
# =========================
def get_portfolio():

    data = {
        "balance": portfolio["balance"],
        "history": portfolio["history"],
        "open_trade": None
    }

    trade = portfolio.get("open_trade")

    if trade:
        symbol = trade["symbol"]

        prices = get_current_price([symbol])
        current_price = prices.get(symbol)

        if current_price:
            entry = trade["entry"]
            qty = trade["quantity"]

            pnl = (current_price - entry) * qty
            pnl_percent = ((current_price - entry) / entry) * 100

            trade_copy = trade.copy()
            trade_copy["current_price"] = round(current_price, 2)
            trade_copy["pnl"] = round(pnl, 2)
            trade_copy["pnl_percent"] = round(pnl_percent, 2)

            data["open_trade"] = trade_copy

    return data


# =========================
# PERFORMANCE
# =========================
def get_performance():
    trades = portfolio["history"]

    total = len(trades)
    wins = len([t for t in trades if t["result"] == "WIN"])
    losses = len([t for t in trades if t["result"] == "LOSS"])

    win_rate = (wins / total * 100) if total > 0 else 0

    return {
        "balance": portfolio["balance"],
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "open_trade": portfolio["open_trade"]
    }