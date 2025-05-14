import schedule
import time
from flask import Flask
from funding import check_all_exchanges  # Updated import path

app = Flask(__name__)

def job():
    print("[INFO] Running funding rate check job...")
    check_all_exchanges()

# Schedule job to run every minute
schedule.every(60).seconds.do(job)

# Define a simple route for health check
@app.route("/")
def health_check():
    return "Funding rate alert bot is running!"

if __name__ == "__main__":
    # Start Flask web service and schedule job
    from threading import Thread

    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    # Start the schedule in a separate thread
    schedule_thread = Thread(target=run_schedule)
    schedule_thread.start()

    # Run Flask server
    app.run(host="0.0.0.0", port=5000)
