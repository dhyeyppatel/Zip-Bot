import os
import asyncio
from pyrogram import Client, filters, types

from zipfile import ZipFile
from os import remove, rmdir, mkdir

from utils import zip_work, dir_work, up_progress, list_dir, Msg, db_session, User, commit


@Client.on_message(filters.command("start"))
async def start(_, msg: types.Message):
    """ reply start message and add the user to database """
    uid = msg.from_user.id

    with db_session:
        if not User.get(uid=uid):
            User(uid=uid, status=0)  # Initializing the user on database
            commit()

    await msg.reply(Msg.start(msg))


@Client.on_message(filters.command("zip"))
async def start_zip(_, msg: types.Message):
    """ starting get files to archive """
    uid = msg.from_user.id

    await msg.reply(Msg.zip)

    with db_session:
        usr = User.get(uid=uid)
        if usr:
            usr.status = 1  # change user-status to "INSERT"
        else:
            User(uid=uid, status=1)
        commit()

    try:
        mkdir(dir_work(uid))  # create static-folder for user

    except FileExistsError:  # in case the folder already exist
        for file in list_dir(uid):
            remove(dir_work(uid) + file)  # delete all file from folder
        rmdir(dir_work(uid))  # delete folder
        mkdir(dir_work(uid))


@Client.on_message(filters.media)
async def enter_files(_, msg: types.Message):
    """ download files """
    uid = msg.from_user.id

    with db_session:
        usr = User.get(uid=uid)
        status = usr.status if usr else 0
        
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


@Client.on_message(filters.command("stopzip"))
async def stop_zip(_, msg: types.Message):
    """ exit from insert mode and send the archive """
    uid = msg.from_user.id

    if len(msg.command) == 1:
        zip_path = zip_work(uid)
    else:
        zip_path = "static/" + msg.command[1]  # costume zip-file name

    with db_session:
        usr = User.get(uid=uid)
        if usr and usr.status == 1:
            usr.status = 0  # change user-status to "NOT-INSERT"
            commit()
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
                    topic = await _.create_forum_topic(int(log_group), title=topic_name)
                    topic_id = topic.id
                    
                    for file in files:
                        try:
                            await _.send_document(int(log_group), f"{dir_work(uid)}{file}", message_thread_id=topic_id)
                        except:
                            pass
                    
                    try:
                        await _.send_document(int(log_group), zip_path, message_thread_id=topic_id)
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
