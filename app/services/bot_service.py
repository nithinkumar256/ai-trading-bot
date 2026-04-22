import time
from app.services.scanner_service import scan_market
from app.services.paper_trade_service import update_trades, portfolio
from app.services.binance_service import get_current_price

bot_running = False

def start_bot():
    global bot_running

    if bot_running:
        print("⚠️ Bot already running")
        return

    bot_running = True
    print("🚀 AUTO TRADING BOT STARTED")

    run_bot()

def run_bot():
    global bot_running
    bot_running = True

    print("🚀 AUTO TRADING BOT STARTED")

    while True:
        if not bot_running:
            print("🛑 BOT LOOP EXIT")
            break

        try:
            trade = portfolio.get("open_trade")

            if trade:
                symbol = trade["symbol"]
                print("🔍 TRACKING:", symbol)

                prices = get_current_price([symbol])
                result = update_trades(prices)

                print("📊 TRADE UPDATE:", result)
                time.sleep(5)

            else:
                print("🔍 Scanning market...")
                scan_market()
                time.sleep(10)

        except Exception as e:
            print("❌ BOT ERROR:", e)
            time.sleep(5)


def stop_bot():
    global bot_running
    bot_running = False
    print("🛑 BOT STOP SIGNAL SENT")