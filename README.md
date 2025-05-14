# Funding Rate Alert Bot

This bot monitors funding rates across multiple crypto exchanges and sends Telegram alerts 15 minutes before funding payments.

### Supported Exchanges
- Binance
- OKX
- MEXC
- Bybit

### Features
- Automatically detects top 5 highest absolute funding rates (positive or negative)
- Sends formatted alerts to a Telegram chat

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/funding-rate-alert-bot.git
cd funding-rate-alert-bot
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Configure your `config.py`:
```python
TELEGRAM_BOT_TOKEN = "your_bot_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"
```

4. Run the bot:
```bash
python main.py
```

### Deployment
- You can deploy this bot to platforms like Render.com using GitHub integration.
