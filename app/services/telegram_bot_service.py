import time
from threading import Thread
from app.services.telegram_service import get_updates, send_telegram
from app.services.bot_service import start_bot, stop_bot
from app.services.paper_trade_service import get_portfolio


def run_telegram_bot():

    print("🤖 Telegram bot started...")

    while True:
        updates = get_updates()

        for update in updates:
            try:
                message = update["message"]["text"]
                chat_id = update["message"]["chat"]["id"]

                print("📩 Command:", message)

                # =========================
                # COMMAND HANDLER
                # =========================

                if message == "/startbot":
                    # ✅ RUN IN BACKGROUND THREAD
                    Thread(target=start_bot, daemon=True).start()
                    send_telegram("🚀 Trading bot started")

                elif message == "/stopbot":
                    stop_bot()
                    send_telegram("🛑 Trading bot stopped")

                elif message == "/portfolio":
                    data = get_portfolio()

                    msg = (
                        f"💼 PORTFOLIO\n\n"
                        f"Balance: {data['balance']}\n"
                    )

                    if data["open_trade"]:
                        trade = data["open_trade"]

                        msg += (
                            f"\n📊 OPEN TRADE\n"
                            f"Symbol: {trade['symbol']}\n"
                            f"Entry: {trade['entry']}\n"
                            f"PnL: {trade.get('pnl', 0)}\n"
                        )

                    send_telegram(msg)

            except Exception as e:
                print("Telegram bot error:", e)

        time.sleep(2)