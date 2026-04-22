def generate_signal(data: dict):
    rsi = data.get("rsi")
    ema9 = data.get("ema9")
    ema21 = data.get("ema21")
    macd = data.get("macd")
    macd_signal = data.get("macd_signal")
    close = data.get("close")
    vwap = data.get("vwap")

    # Default
    decision = "HOLD"
    reason = "No clear signal"

    # 🟢 BUY CONDITIONS
    if (
        rsi is not None and rsi < 35 and
        ema9 > ema21 and
        macd > macd_signal and
        close > vwap
    ):
        decision = "BUY"
        reason = "Oversold + Uptrend + Bullish momentum + Above VWAP"

    # 🔴 SELL CONDITIONS
    elif (
        rsi is not None and rsi > 65 and
        ema9 < ema21 and
        macd < macd_signal and
        close < vwap
    ):
        decision = "SELL"
        reason = "Overbought + Downtrend + Bearish momentum + Below VWAP"

    return {
        "decision": decision,
        "reason": reason
    }