import schedule
import time
from flask import Flask
from funding import check_all_exchanges, send_telegram_alert

app = Flask(__name__)

# Scheduled job to check funding rates
def job():
    print("[INFO] Running funding rate check job...")
    check_all_exchanges()

# Test function to send a message when app starts
def send_test_message():
    test_message = "This is a test message from your funding rate alert bot!"
    send_telegram_alert(test_message)

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
