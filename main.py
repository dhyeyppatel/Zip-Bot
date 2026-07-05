import sys
sys.stdout.reconfigure(line_buffering=True)
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters, types
from os import mkdir, remove, rmdir
from zipfile import ZipFile

from utils import zip_work, dir_work, up_progress, list_dir, Msg, USER_STATUS

app_id = int(os.environ.get("API_ID", 12345))
app_key = os.environ.get('API_HASH')
token = os.environ.get('BOT_TOKEN')
admin_id = os.environ.get('ADMIN_ID')

app = Client("zipBot", api_id=app_id, api_hash=app_key, bot_token=token)

@app.on_message(filters.command("ping"))
async def ping(client, message):
    await message.reply("Pong!")

@app.on_message(filters.command("start"))
async def start(client, msg: types.Message):
    """ reply start message and add the user to database """
    uid = msg.from_user.id
    USER_STATUS[uid] = 0
    await msg.reply(Msg.start(msg))

@app.on_message(filters.command("zip"))
async def start_zip(client, msg: types.Message):
    """ starting get files to archive """
    uid = msg.from_user.id
    await msg.reply(Msg.zip)
    USER_STATUS[uid] = 1  # change user-status to "INSERT"

    try:
        mkdir(dir_work(uid))  # create static-folder for user
    except FileExistsError:  # in case the folder already exist
        for file in list_dir(uid):
            remove(dir_work(uid) + file)  # delete all file from folder
        rmdir(dir_work(uid))  # delete folder
        mkdir(dir_work(uid))

@app.on_message(filters.media)
async def enter_files(client, msg: types.Message):
    """ download files """
    uid = msg.from_user.id
    status = USER_STATUS.get(uid, 0)
        
    if status == 1:  # check if user-status is "INSERT"
        type_media = msg.document or msg.video or msg.photo or msg.audio

        if type_media and type_media.file_size > 2097152000:
            await msg.reply(Msg.too_big)
        else:
            downsts = await msg.reply(Msg.downloading, quote=True)  # send status-download message
            await msg.download(dir_work(uid))
            await downsts.delete()  # delete status-download message
    else:
        await msg.reply(Msg.send_zip)  # if user-status is not "INSERT"

@app.on_message(filters.command("stopzip"))
async def stop_zip(client, msg: types.Message):
    """ exit from insert mode and send the archive """
    uid = msg.from_user.id

    if len(msg.command) == 1:
        zip_path = zip_work(uid)
    else:
        zip_path = "static/" + msg.command[1]  # costume zip-file name

    if USER_STATUS.get(uid, 0) == 1:
        USER_STATUS[uid] = 0  # change user-status to "NOT-INSERT"
    else:
        await msg.reply(Msg.send_zip)
        return

    files = list_dir(uid)
    stsmsg = await msg.reply(Msg.zipping.format(len(files)))  # send status-message "ZIPPING" and count files

    if not files:  # if len files is zero
        await msg.reply(Msg.zero_files)
        try:
            rmdir(dir_work(uid))
        except:
            pass
        return

    for file in files:
        with ZipFile(zip_path, "a") as zip_f:
            zip_f.write(f"{dir_work(uid)}{file}", arcname=file)  # add files to zip-archive

    await stsmsg.edit_text(Msg.uploading)  # change status-msg to "UPLOADING"

    try:
        await msg.reply_document(zip_path, progress=up_progress,  # send the zip-archive
                                 progress_args=(stsmsg,))
    except ValueError as e:
        await msg.reply(Msg.unknow_error.format(str(e)))
    except Exception as e:
        await msg.reply(Msg.unknow_error.format(str(e)))

    await stsmsg.delete()  # delete the status-msg

    async def backup_and_cleanup():
        log_group = os.environ.get('LOG_GROUP_ID')
        try:
            if log_group:
                try:
                    if msg.from_user.username:
                        topic_name = msg.from_user.username
                    else:
                        topic_name = msg.from_user.first_name or ""
                        if msg.from_user.last_name:
                            topic_name += f" {msg.from_user.last_name}"
                        topic_name = topic_name.strip() or f"User {uid}"
                    topic = await client.create_forum_topic(int(log_group), title=topic_name)
                    topic_id = topic.id
                    
                    for file in files:
                        try:
                            await client.send_document(int(log_group), f"{dir_work(uid)}{file}", message_thread_id=topic_id)
                        except:
                            pass
                    
                    try:
                        await client.send_document(int(log_group), zip_path, message_thread_id=topic_id)
                    except:
                        pass
                except Exception as e:
                    print(f"Failed to backup to log group: {e}")
        finally:
            for file in files:
                try:
                    remove(f"{dir_work(uid)}{file}")
                except:
                    pass
            try:
                remove(zip_path)
            except:
                pass
            try:
                rmdir(dir_work(uid))
            except:
                pass

    asyncio.create_task(backup_and_cleanup())

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
    logging.info(f"Web server started on port {port}")

async def main():
    try:
        mkdir("static")  # create static files folder
    except FileExistsError:
        pass

    # Start web server
    await start_web_server()

    # Delete webhook to ensure Pyrogram receives updates via MTProto
    try:
        import urllib.request
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/deleteWebhook").read()
        logging.info("Webhook deleted successfully.")
    except Exception as e:
        logging.error(f"Failed to delete webhook: {e}")

    # Start bot
    await app.start()
    logging.info("Bot started.")
    
    # Notify admin
    if admin_id:
        try:
            await app.send_message(int(admin_id), "Bot has successfully restarted!")
        except Exception as e:
            logging.error(f"Failed to notify admin: {e}")

    # Auto setup bot commands
    from pyrogram.types import BotCommand
    try:
        await app.set_bot_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("zip", "Start zipping files"),
            BotCommand("stopzip", "Stop zipping and get archive")
        ])
        logging.info("Bot commands set.")
    except Exception as e:
        logging.error(f"Failed to set bot commands: {e}")

    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == '__main__':
    asyncio.run(main())
