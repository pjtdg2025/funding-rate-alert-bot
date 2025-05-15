import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

# === Configuration ===
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)

# === Funding Rate Fetch Functions ===
async def fetch_binance():
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        data = res.json()
        return [
            {
                "exchange": "Binance",
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
        now = datetime.utcnow()
        # Assuming Bybit uses fixed 8h intervals at 00:00, 08:00, 16:00 UTC
        next_hour = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        funding_time = min(
            h for h in [0, 8, 16] if h > now.hour
        ) if now.hour < 16 else 0
        next_funding = datetime(now.year, now.month, now.day, funding_time)
        if next_funding < now:
            next_funding += timedelta(days=1)

        return [
            {
                "exchange": "Bybit",
                "symbol": x["symbol"],
                "fundingRate": float(x.get("funding_rate", 0.0)),
                "nextFundingTime": int(next_funding.timestamp()),
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
                "exchange": "OKX",
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
                "exchange": "MEXC",
                "symbol": x["symbol"],
                "fundingRate": float(x["fundingRate"]),
                "nextFundingTime": int(x["nextFundingTime"] / 1000),
            }
            for x in tickers
        ]

# === Alert Logic ===
async def check_funding_rates():
    logging.info("🔍 Checking funding rates...")
    fetchers = [fetch_binance(), fetch_bybit(), fetch_okx(), fetch_mexc()]
    results = await asyncio.gather(*fetchers, return_exceptions=True)

    all_rates = []
    for result in results:
        if isinstance(result, list):
            all_rates.extend(result)

    now = int(datetime.utcnow().timestamp())
    window = 2700  # 45 minutes

    alerts_by_exchange = {}
    for r in all_rates:
        time_diff = r["nextFundingTime"] - now
        if 0 < time_diff <= window:
            alerts_by_exchange.setdefault(r["exchange"], []).append(r)

    if not alerts_by_exchange:
        logging.info("⏳ No funding rates 45 min before settlement.")
        return

    msg_lines = ["⚠️ Top Funding Rates (45 min before settlement):"]
    for exchange, rates in alerts_by_exchange.items():
        sorted_rates = sorted(rates, key=lambda x: x["fundingRate"])
        top_neg = sorted_rates[:3]
        top_pos = sorted_rates[-3:][::-1]
        msg_lines.append(f"\n📌 {exchange}:")
        for r in top_neg:
            msg_lines.append(f"🔻 {r['symbol']} — {r['fundingRate']*100:.4f}%")
        for r in top_pos:
            msg_lines.append(f"🔺 {r['symbol']} — {r['fundingRate']*100:.4f}%")

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
