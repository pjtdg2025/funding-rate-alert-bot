import schedule
import time
import os
import requests
from flask import Flask
from funding import check_all_exchanges

app = Flask(__name__)

# Scheduled job to check funding rates
def job():
    print("[INFO] Running funding rate check job...")
    check_all_exchanges()

# Function to send a test message on startup with debug logs
def send_test_message():
    test_message = "This is a test message from your funding rate alert bot!"
    print("[DEBUG] Sending test message...")
    print("[DEBUG] BOT TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))
    print("[DEBUG] CHAT ID:", os.getenv("TELEGRAM_CHAT_ID"))
    send_telegram_alert(test_message)

# Send a Telegram alert
def send_telegram_alert(message):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        print("[ERROR] Missing Telegram credentials")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
    print(f"[DEBUG] Telegram response: {response.status_code} - {response.text}")

# Schedule job to run every 60 seconds
schedule.every(60).seconds.do(job)

@app.route("/")
def health_check():
    return "Funding rate alert bot is running!"

# Send test message once on startup
send_test_message()

if __name__ == "__main__":
    from threading import Thread

    # Background thread for running the scheduled job
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    schedule_thread = Thread(target=run_schedule)
    schedule_thread.start()

    # Start Flask server
    app.run(host="0.0.0.0", port=5000)
