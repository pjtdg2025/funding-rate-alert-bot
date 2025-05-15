import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from aiohttp import web
import os

# === CONFIG ===
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
EXCHANGES = ["binance", "bybit", "okx", "mexc"]
bot = Bot(token=BOT_TOKEN)

logging.basicConfig(level=logging.INFO)

# === FETCH FUNDING DATA ===
async def fetch_binance():
    async with httpx.AsyncClient() as client:
        res = await client.get("https://fapi.binance.com/fapi/v1/premiumIndex")
        data = res.json()
        return [
            {
                "exchange": "binance",
                "symbol": x["symbol"],
                "fundingRate": float(x["lastFundingRate"]),
                "nextFundingTime": int(x["nextFundingTime"]) // 1000,
            }
            for x in data
        ]

async def fetch_bybit():
    url = "https://api.bybit.com/v2/public/tickers"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        tickers = res.json()["result"]
        now = datetime.utcnow()
        next_time = int((now + timedelta(hours=8 - now.hour % 8, minutes=-now.minute, seconds=-now.second)).timestamp())
        return [
            {
                "exchange": "bybit",
                "symbol": x["symbol"],
                "fundingRate": float(x.get("funding_rate", 0.0)),
                "nextFundingTime": next_time,
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
                "exchange": "okx",
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
                "exchange": "mexc",
                "symbol": x["symbol"],
                "fundingRate": float(x["fundingRate"]),
                "nextFundingTime": int(x["nextFundingTime"] / 1000),
            }
            for x in tickers
        ]

# === MAIN LOGIC ===
async def check_funding_rates():
    logging.info("🔍 Checking funding rates...")
    fetchers = [fetch_binance(), fetch_bybit(), fetch_okx(), fetch_mexc()]
    all_rates = []
    now = int(datetime.utcnow().timestamp())

    results = await asyncio.gather(*fetchers, return_exceptions=True)
    for r in results:
        if isinstance(r, list):
            all_rates.extend(r)

    upcoming = [
        r for r in all_rates if 0 < (r["nextFundingTime"] - now) <= 2700  # 45 minutes
    ]

    if not upcoming:
        logging.info("⏳ No funding rates due in 45 minutes.")
        return

    # Group by exchange and sort
    grouped = {}
    for r in upcoming:
        grouped.setdefault(r["exchange"], []).append(r)

    messages = []
    for exchange, rates in grouped.items():
        top_positive = sorted([x for x in rates if x["fundingRate"] > 0], key=lambda x: -x["fundingRate"])[:3]
        top_negative = sorted([x for x in rates if x["fundingRate"] < 0], key=lambda x: x["fundingRate"])[:3]
        if not top_positive and not top_negative:
            continue
        messages.append(f"📊 *{exchange.upper()}*")
        for x in top_positive:
            messages.append(f"🟢 {x['symbol']}: +{x['fundingRate']*100:.4f}%")
        for x in top_negative:
            messages.append(f"🔴 {x['symbol']}: {x['fundingRate']*100:.4f}%")

    if messages:
        await bot.send_message(chat_id=CHAT_ID, text="\n".join(messages), parse_mode="Markdown")
        logging.info("✅ Alert sent.")
    else:
        logging.info("🟡 No extreme funding rates found.")

# === TELEGRAM /status COMMAND ===
async def handle_webhook(request):
    data = await request.json()
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id", "")

    if text == "/status":
        await bot.send_message(chat_id=chat_id, text="✅ Bot is running and monitoring funding rates.")
    return web.Response()

# === MAIN ENTRY ===
async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_funding_rates, "interval", minutes=5)
    scheduler.start()
    logging.info("🚀 Funding rate monitor running 24/7...")

    # Webhook for /status command
    app = web.Application()
    app.router.add_post("/webhook", handle_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 5000)))
    await site.start()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
