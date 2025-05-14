import requests
import os
from datetime import datetime
from time import sleep

# Get Telegram bot credentials from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Function to send alerts via Telegram
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.get(url, params=params)
    return response.json()

# Function to check funding rates from exchanges
def check_funding_rate(exchange, symbol):
    if exchange == "binance":
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}"
    elif exchange == "okx":
        url = f"https://www.okx.com/api/v5/market/funding-rate?instId={symbol}"
    elif exchange == "mexc":
        url = f"https://www.mexc.com/api/v2/market/funding-rate/{symbol}"
    else:
        return None
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to find the highest funding rates and send an alert
def check_all_exchanges():
    exchanges = ["binance", "okx", "mexc"]
    symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]  # Add more symbols as needed
    for exchange in exchanges:
        for symbol in symbols:
            data = check_funding_rate(exchange, symbol)
            if data:
                # Here we can use data to calculate and filter out the highest funding rates
                funding_rate = data[0]["fundingRate"] if isinstance(data, list) else data.get("fundingRate")
                if funding_rate:
                    message = f"Funding rate for {symbol} on {exchange}: {funding_rate}."
                    send_telegram_alert(message)

# Keep the bot running and check funding rates
if __name__ == "__main__":
    while True:
        print(f"[INFO] Checking funding rates at {datetime.now()}")
        check_all_exchanges()
        sleep(60)  # Check every 60 seconds (or adjust the interval)
