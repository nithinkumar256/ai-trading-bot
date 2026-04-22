from app.services.binance_service import get_klines
from app.services.indicator_service import calculate_indicators
from app.services.scanner_service import calculate_score
from app.services.risk_service import calculate_trade_levels, calculate_position


def backtest(symbol="BTCUSDT", initial_balance: float = 10000.0):

    # =========================
    # DATA
    # =========================
    df_5m = calculate_indicators(get_klines(symbol, "5m"))
    df_15m = calculate_indicators(get_klines(symbol, "15m"))

    balance = float(initial_balance)
    position = None
    trades = []

    min_len = min(len(df_5m), len(df_15m))

    start = 50  # warmup candles

    # =========================
    # LOOP
    # =========================
    for i in range(start, min_len):

        row_5m = df_5m.iloc[i]
        row_15m = df_15m.iloc[i]

        # =========================
        # INDICATORS (SAFE)
        # =========================
        rsi_5m = row_5m.get("rsi")
        close_5m = row_5m.get("close")
        vwap_5m = row_5m.get("vwap")

        ema9_15m = row_15m.get("ema9")
        ema21_15m = row_15m.get("ema21")

        # skip invalid data
        if rsi_5m is None or close_5m is None or vwap_5m is None:
            continue

        # =========================
        # TREND (same logic as scanner)
        # =========================
        trend = "SIDEWAYS"
        if ema9_15m is not None and ema21_15m is not None:
            if ema9_15m > ema21_15m:
                trend = "UP"
            elif ema9_15m < ema21_15m:
                trend = "DOWN"

        # =========================
        # SCORE
        # =========================
        score = calculate_score(row_5m)
        if score is None:
            score = 0

        # DEBUG (optional - uncomment if needed)
        # if trend == "UP":
        #     print(symbol, score, rsi_5m, close_5m, vwap_5m)

        # =========================
        # ENTRY (FIXED LOGIC)
        # =========================
        if position is None:

            if (
                trend == "UP" and
                score >= 50 and
                rsi_5m <= 65 and
                close_5m >= vwap_5m * 0.995
            ):

                trade_levels = calculate_trade_levels(row_5m)

                if trade_levels:

                    qty = calculate_position(
                        trade_levels["entry"],
                        trade_levels["stop_loss"]
                    )

                    position = {
                        "entry": trade_levels["entry"],
                        "stop_loss": trade_levels["stop_loss"],
                        "take_profit": trade_levels["take_profit"],
                        "quantity": qty
                    }

        # =========================
        # EXIT
        # =========================
        else:

            high = row_5m.get("high")
            low = row_5m.get("low")

            entry = position["entry"]
            sl = position["stop_loss"]
            tp = position["take_profit"]
            qty = position["quantity"]

            # TAKE PROFIT
            if high is not None and high >= tp:
                profit = (tp - entry) * qty
                balance += profit

                trades.append({
                    "type": "WIN",
                    "profit": profit
                })

                position = None

            # STOP LOSS
            elif low is not None and low <= sl:
                loss = (entry - sl) * qty
                balance -= loss

                trades.append({
                    "type": "LOSS",
                    "profit": -loss
                })

                position = None

    # =========================
    # RESULTS
    # =========================
    total_trades = len(trades)
    wins = len([t for t in trades if t["type"] == "WIN"])
    losses = len([t for t in trades if t["type"] == "LOSS"])

    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    return {
        "symbol": symbol,
        "final_balance": round(balance, 2),
        "profit": round(balance - initial_balance, 2),
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2)
    }