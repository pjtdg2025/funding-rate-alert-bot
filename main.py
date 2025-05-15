import logging
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- Configuration ---
TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your bot token
WEBHOOK_URL = "https://YOUR_RENDER_URL_HERE/webhook"  # Replace with your Render domain
PORT = 10000  # Port Render uses for web service

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask-style aiohttp webhook handler ---
async def telegram_webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response()
    except Exception as e:
        logger.error(f"Error in webhook handler: {e}")
        return web.Response(status=500)

# --- /start command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running!")

# --- TEMP handler to log your chat ID ---
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logger.info(f"👤 User Chat ID: {chat_id}")
    await update.message.reply_text(f"Your chat ID is: {chat_id}")

# --- Periodic task example ---
async def periodic_task():
    logger.info("Running scheduled task...")

# --- Main async entry point ---
async def main():
    global application  # So it's accessible in the webhook handler
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_chat_id))  # TEMP

    # Start scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(periodic_task, "interval", minutes=1)
    scheduler.start()

    # Start the Telegram bot
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info("✅ Webhook was successfully set.")
    await application.start()
    logger.info("🚀 Bot is live and webhook server is running.")

    # Start aiohttp webhook server
    app = web.Application()
    app.router.add_post("/webhook", telegram_webhook_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
