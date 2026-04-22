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

    # ✅ validate first
    if "symbol" not in trade:
        return {"error": "symbol missing"}

    if portfolio["open_trade"] is not None:
        return {"message": "Trade already open"}

    portfolio["open_trade"] = trade

    # ✅ send telegram AFTER success
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
    sl = trade["stop_loss"]
    tp = trade["take_profit"]
    qty = trade["quantity"]

    # =========================
    # TAKE PROFIT
    # =========================
    if price >= tp:
        profit = (tp - entry) * qty
        portfolio["balance"] += profit

        result = {
            "symbol": symbol,
            "result": "WIN",
            "profit": round(profit, 2)
        }

        send_telegram(
            f"✅ TRADE WON\n\n"
            f"Symbol: {symbol}\n"
            f"Profit: {round(profit, 2)}\n"
            f"Balance: {round(portfolio['balance'], 2)}"
        )

        portfolio["history"].append(result)
        portfolio["open_trade"] = None

        return result

    # =========================
    # STOP LOSS
    # =========================
    elif price <= sl:
        loss = (entry - sl) * qty
        portfolio["balance"] -= loss

        result = {
            "symbol": symbol,
            "result": "LOSS",
            "profit": round(-loss, 2)
        }

        send_telegram(
            f"❌ TRADE LOST\n\n"
            f"Symbol: {symbol}\n"
            f"Loss: {round(loss, 2)}\n"
            f"Balance: {round(portfolio['balance'], 2)}"
        )

        portfolio["history"].append(result)
        portfolio["open_trade"] = None

        return result

    return {
        "message": "Trade still open",
        "current_price": price
    }


# =========================
# PORTFOLIO (LIVE PnL)
# =========================
def get_portfolio():

    # ✅ safe copy
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