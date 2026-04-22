from fastapi import APIRouter
from app.services.binance_service import get_klines, get_current_price
from app.services.indicator_service import calculate_indicators
from app.services.strategy_service import generate_signal
from app.services.scanner_service import scan_market, pick_best_trade
from app.services.paper_trade_service import get_performance, update_trades
from app.services.backtest_service import backtest
from app.services.paper_trade_service import update_trades, portfolio
from app.services.binance_service import get_current_price
from app.services.paper_trade_service import (
    update_trades,
    get_portfolio,
    portfolio
)
from app.services.binance_service import get_current_price
from app.services.bot_service import run_bot, stop_bot
import threading
from threading import Thread
from app.services.telegram_bot_service import run_telegram_bot

telegram_thread = None

bot_thread = None
bot_running = False
router = APIRouter()


@router.get("/")
def root():
    return {"message": "AI Trading Bot is running"}


@router.get("/market-data")
def market_data(symbol: str = "BTCUSDT", interval: str = "1m"):
    df = get_klines(symbol, interval)

    return {
        "symbol": symbol,
        "interval": interval,
        "data": df.tail(5).to_dict(orient="records")
    }


@router.get("/indicators")
def indicators(symbol: str = "BTCUSDT", interval: str = "1m"):
    df = get_klines(symbol, interval)
    df = calculate_indicators(df)

    latest = df.tail(1).to_dict(orient="records")[0]

    return {
        "symbol": symbol,
        "interval": interval,
        "indicators": latest
    }


@router.get("/signal")
def get_signal(symbol: str = "BTCUSDT", interval: str = "1m"):
    df = get_klines(symbol, interval)
    df = calculate_indicators(df)

    latest = df.tail(1).to_dict(orient="records")[0]
    signal = generate_signal(latest)

    return {
        "symbol": symbol,
        "interval": interval,
        "indicators": latest,
        "signal": signal
    }


# ✅ FIXED SCANNER ROUTE
@router.get("/scan")
def scan(limit: int = 30):
    results = scan_market(limit=limit)
    best_trade = pick_best_trade(results)

    return {
        "scanned_trades": results,
        "best_trade": best_trade
    }


# ✅ NEW: Update trades (SL/TP check)
@router.get("/update-trades")
def update_trades_api():

    trade = portfolio.get("open_trade")

    if not trade:
        return {"message": "No open trade"}

    symbol = trade["symbol"]

    prices = get_current_price([symbol])

    return update_trades(prices)


# ✅ NEW: Performance tracking
@router.get("/performance")
def performance():
    return get_performance()

@router.get("/backtest")
def run_backtest(
    symbol: str = "BTCUSDT",
    initial_balance: float = 10000
):
    return backtest(symbol, initial_balance)

@router.get("/portfolio")
def portfolio_api():
    return get_portfolio()


@router.get("/start-bot")
def start_bot():
    global bot_thread

    if bot_thread and bot_thread.is_alive():
        return {"message": "Bot already running"}

    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    return {"message": "🚀 Bot started"}


@router.get("/stop-bot")
def stop_bot_api():
    stop_bot()
    return {"message": "🛑 Bot stopping"}

@router.get("/start-telegram")
def start_telegram():

    global telegram_thread

    if telegram_thread is None:
        telegram_thread = Thread(target=run_telegram_bot, daemon=True)
        telegram_thread.start()

    return {"message": "Telegram bot started"}