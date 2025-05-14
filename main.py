import schedule
import time
from utils.funding import check_all_exchanges

def job():
    print("[INFO] Running funding rate check job...")
    check_all_exchanges()

# Run the job every minute (you can change this if needed)
schedule.every(60).seconds.do(job)

print("[INFO] Funding rate alert bot started.")

while True:
    schedule.run_pending()
    time.sleep(1)
