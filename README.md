# Zip Bot

A telegram bot that allows compression of multiple files into a ZIP archive, upgraded for deployment on Render. It features asynchronous operation using Pyrogram v2, a dummy web server to keep it alive on Render, and automatic background backups.

## Features
- Zip multiple files simultaneously (up to 500 files, max 2GB limit per Telegram API).
- Automatic topic-based backups to a specified log group.
- Start-up notifications to administrators.
- Built-in dummy web server to pass Render health checks.

## Deploy to Render

You can deploy this directly to Render as a **Web Service**. 

Make sure to set the following Environment Variables in your Render Dashboard:
- `API_ID`: Your Telegram API ID.
- `API_HASH`: Your Telegram API Hash.
- `BOT_TOKEN`: Your bot token from BotFather.
- `ADMIN_ID`: Your Telegram User ID (to receive a startup notification).
- `LOG_GROUP_ID`: The Chat ID of the group where the bot will backup files (must start with `-100`).

## Deploy Locally

Clone the repository:

```bash
git clone https://github.com/dhyeyppatel/Zip-Bot.git
cd Zip-Bot
```

Install requirements:

```bash
pip3 install -r requirements.txt
```

Set Environment Variables:

You can set the environment variables locally before running:
```bash
export API_ID="123456"
export API_HASH="abcdef1234"
export BOT_TOKEN="1234567890:ABCDEF"
export ADMIN_ID="12345678"
export LOG_GROUP_ID="-100123456789"
```

Run the bot:

```bash
python3 main.py
```
