import os
import asyncio
from aiohttp import web
from pyrogram import Client
from os import mkdir

app_id = int(os.environ.get("API_ID", 12345))
app_key = os.environ.get('API_HASH')
token = os.environ.get('BOT_TOKEN')
admin_id = os.environ.get('ADMIN_ID')

app = Client("zipBot", api_id=app_id, api_hash=app_key, bot_token=token, plugins=dict(root="bot"))

async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    server = web.Application()
    server.add_routes([web.get('/', handle)])
    runner = web.AppRunner(server)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

async def main():
    try:
        mkdir("static")  # create static files folder
    except FileExistsError:
        pass

    # Start web server
    await start_web_server()

    # Start bot
    await app.start()
    print("Bot started.")
    
    # Notify admin
    if admin_id:
        try:
            await app.send_message(int(admin_id), "Bot has successfully restarted!")
        except Exception as e:
            print(f"Failed to notify admin: {e}")

    # Auto setup bot commands
    from pyrogram.types import BotCommand
    try:
        await app.set_bot_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("zip", "Start zipping files"),
            BotCommand("stopzip", "Stop zipping and get archive")
        ])
        print("Bot commands set.")
    except Exception as e:
        print(f"Failed to set bot commands: {e}")

    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == '__main__':
    asyncio.run(main())
