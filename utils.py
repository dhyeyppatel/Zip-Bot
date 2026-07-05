from pyrogram.types import Message
from os import listdir

USER_STATUS = {}


# ========= helping func =========
def dir_work(uid: int) -> str:
    """ static-user folder """
    return f"static/{uid}/"


def zip_work(uid: int) -> str:
    """ zip-archive file """
    return f'static/{uid}.zip'


def list_dir(uid: int) -> list:
    """ items in static-user folder """
    return listdir(dir_work(uid))


async def up_progress(current, total, msg: Message):
    """ edit status-msg with progress of the uploading """
    await msg.edit(f"**Upload progress: {current * 100 / total:.1f}%**")


# ========= MSG class =========
class Msg:

    def start(msg: Message) -> str:
        """ return start-message text """
        txt = f"Hey {msg.from_user.mention}!\n" \
              "\nI can compress files in to an archive." \
              "\nJust send /zip, and follow the instructions."
        return txt

    zip = "Send the files you want to compress, and at the end send /stopzip after all the files have been downloaded.\n" \
          "\n\nNote: due to upload limit, the total size of the file(s) can be at most 2GB."
    too_big = "Note: due to upload limit, the total size of the file(s) can be at most 2GB."
    send_zip = "Send /zip to compress the files"
    zipping = "start compressing {} files..."
    uploading = "uploading archive..."
    unknow_error = "An unknown error occurred"
    downloading = "downloading..."
    zero_files = "No files were sent"
