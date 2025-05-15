import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

# === Configuration ===
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
EXCHANGES = ["binance", "bybit", "okx", "mexc"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)

# === Funding Rate Fetch Functions ===
async def fetch_binance():
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    params = {"limit": 1}
    async with httpx.AsyncClient() as client:
        res = await client.get("https://fapi.binance.com/fapi/v1/premiumIndex")
        data = res.json()
        return [
            {
                "symbol": x["symbol"],
                "fundingRate": float(x["lastFundingRate"]),
                "nextFundingTime": int(x["nextFundingTime"]),
            }
            for x in data
        ]

async def fetch_bybit():
    url = "https://api.bybit.com/v2/public/tickers"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        tickers = res.json()["result"]
        return [
            {
                "symbol": x["symbol"],
                "fundingRate": float(x.get("funding_rate", 0.0)),
                "nextFundingTime": int(datetime.utcnow().timestamp() + 60 * 60 * 8),
            }
            for x in tickers if x["symbol"].endswith("USDT")
        ]

async def fetch_okx():
    url = "https://www.okx.com/api/v5/public/funding-rate?instType=SWAP"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        tickers = res.json()["data"]
        return [
            {
                "symbol": x["instId"],
                "fundingRate": float(x["fundingRate"]),
                "nextFundingTime": int(datetime.strptime(x["fundingTime"], "%Y-%m-%dT%H:%M:%SZ").timestamp()),
            }
            for x in tickers
        ]

async def fetch_mexc():
    url = "https://contract.mexc.com/api/v1/contract/funding_rate"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        tickers = res.json()["data"]
        return [
            {
                "symbol": x["symbol"],
                "fundingRate": float(x["fundingRate"]),
                "nextFundingTime": int(x["nextFundingTime"] / 1000),
            }
            for x in tickers
        ]

# === Alert Logic ===
async def check_funding_rates():
    logging.info("🔍 Checking funding rates...")
    all_rates = []

    fetchers = [fetch_binance(), fetch_bybit(), fetch_okx(), fetch_mexc()]
    results = await asyncio.gather(*fetchers, return_exceptions=True)

    for result in results:
        if isinstance(result, list):
            all_rates.extend(result)

    now = int(datetime.utcnow().timestamp())
    upcoming = [
        r for r in all_rates if 0 < (r["nextFundingTime"] - now) <= 900  # within 15 min
    ]

    if not upcoming:
        logging.info("⏳ No upcoming funding payments within 15 minutes.")
        return

    sorted_rates = sorted(upcoming, key=lambda x: abs(x["fundingRate"]), reverse=True)[:5]
    msg_lines = ["⚠️ Top 5 Upcoming Funding Rates (Next 15min):"]
    for r in sorted_rates:
        msg_lines.append(f"🔹 {r['symbol']} — {r['fundingRate'] * 100:.4f}%")

    msg = "\n".join(msg_lines)
    await bot.send_message(chat_id=CHAT_ID, text=msg)
    logging.info("✅ Alert sent.")

# === Main Application ===
async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_funding_rates, "interval", minutes=5)
    scheduler.start()

    logging.info("🚀 Funding rate monitor running 24/7...")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
