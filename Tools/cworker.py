from TG.storage import Queue, igrone_error, retry_on_flood, get_quality_num
from Tools.logger import get_logger
from Tools.db import uts, ensure_user, track_message, messages
from Tools.Helpers import Downloader, progress_for_pyrogram
from bot import Bot, Vars
from time import time
import os
import asyncio
from datetime import datetime, timedelta

logger = get_logger(__name__)

_delete_engine_running = False

def get_random_folder_name(base_folder: str = "Downloads"):
    while True:
        folder_path = f"{base_folder}/{os.urandom(10).hex()}"
        if not os.path.exists(folder_path):
            return folder_path

# ==========================================
# BACKGROUND TASK: 6-HOUR AUTO-DELETE
# ==========================================
async def auto_delete_engine():
    global _delete_engine_running
    if _delete_engine_running:
        return
    _delete_engine_running = True
    
    logger.info("6-Hour Auto-Delete Engine Started.")
    while True:
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=6)
            expired_messages = messages.find({"createdAt": {"$lte": cutoff_time}})
            
            for msg in expired_messages:
                try:
                    await Bot.delete_messages(chat_id=msg["chat_id"], message_ids=msg["message_id"])
                    logger.info(f"Auto-Deleted message {msg['message_id']} from chat {msg['chat_id']}")
                except Exception as e:
                    logger.warning(f"Failed to delete message {msg['message_id']}: {e}")
                finally:
                    messages.delete_one({"_id": msg["_id"]})
                    
        except Exception as e:
            logger.error(f"Auto-Delete Engine Error: {e}")
            
        await asyncio.sleep(60)

async def episode_worker(worker_id):
    if worker_id == 0:
        asyncio.create_task(auto_delete_engine())
        
    while True:
        try:
            data, user_id, task_id = await Queue.get()
            try:
                await episode_download_processer(data, user_id, task_id)
                logger.info(f"Task {task_id} completed by worker {worker_id}")
            except Exception as err:
                logger.error(f"Worker {worker_id} error: {err}")
            finally:
                await Queue.task_done(task_id)
        except Exception as err:
            logger.error(f"Worker {worker_id} queue error: {err}")
            await asyncio.sleep(2)

def clean_name(txt, length=-1):
    txt = txt.replace("_", " ").replace("&", "").replace(";", "")
    txt = txt.replace("None", "").replace(":", "").replace("'", "")
    txt = txt.replace("|", "").replace("*", "").replace("?", "")
    txt = txt.replace(">", "").replace("<", "").replace("`", "")
    txt = txt.replace("!", "").replace("@", "").replace("#", "")
    txt = txt.replace("$", "").replace("%", "").replace("^", "")
    txt = txt.replace("~", "").replace("+", "").replace("=", "")
    txt = txt.replace("/", "").replace("\\", "").replace("\n", "")
    txt = txt.replace(".jpg", "")
    return txt[:length] if length != -1 else txt

async def episode_download_processer(download_, user_id, task_id):
    user_id = str(user_id)
    await ensure_user(user_id)
    sts = download_.sts

    if not download_.download_link or download_.download_link.get('link', None) is None:
        if sts:
            await retry_on_flood(sts.edit_text)("<code>Extraction failed. No high-speed link found.</code>")
        return

    try:
        quality_ = get_quality_num(download_.quality) or "High-Speed"
        file_name = f"✲『SCANIME』✲ {clean_name(download_.anime_title)} - {download_.title} [{quality_}].mp4"
        
        if sts:
            await igrone_error(sts.edit_text)(
                f"<blockquote><b>⚡️ EXTRACTING HIGH-SPEED CDN ⚡️</b></blockquote>\n\n<b>Target:</b> <code>{file_name}</code>\n<b>Task ID:</b> <code>{task_id}</code>"
            )
        
        yt = Downloader(message=sts, file_name=file_name, folder=get_random_folder_name())
        file_path = await yt.download(
            download_.download_link['link'],
            video_format=download_.download_link.get("video_format", "")
        )
        
        if not file_path:
            await yt.clean_folder()
            if sts:
                await igrone_error(sts.edit_text)("<code>Download failed. Server rejected connection.</code>")
            return
            
        if sts:
            await igrone_error(sts.edit_text)("<code>Download complete. Initiating high-speed upload...</code>")

        if isinstance(file_path, list):
            for fp in file_path:
                await send_media(fp, file_name, user_id, sts, download_.download_link['link'])
        else:
            await send_media(file_path, file_name, user_id, sts, download_.download_link['link'])

    except Exception as err:
        logger.exception(err)
        if sts:
            await igrone_error(sts.edit_text)(f"<code>System Error: {err}</code>")
    finally:
        if 'yt' in locals():
            await yt.clean_folder()
        if 'file_path' in locals():
            paths = file_path if isinstance(file_path, list) else [file_path]
            for p in paths:
                if p and os.path.exists(p):
                    try: os.remove(p)
                    except: pass
        
        if sts:
            await retry_on_flood(sts.edit_text)("<code>Task completed.</code>")
            await track_message(sts.chat.id, sts.id)

async def send_media(dl_location, new_filename, user_id, sts, link=None):
    user_id = str(user_id)
    
    caption = f"<blockquote><b>✲『SCANIME』✲ DIRECT DELIVERY</b></blockquote>\n\n<b>File:</b> <code>{new_filename}</code>\n<b>Status:</b> <i>File will self-destruct from the bot chat in 6 hours to protect the server.</i>"
    
    docs = None
    try:
        docs = await retry_on_flood(Bot.send_video)(
            chat_id=int(user_id),
            video=dl_location,
            caption=caption,
            supports_streaming=True,
            file_name=new_filename,
            progress=progress_for_pyrogram,
            progress_args=("<b>⚡️ UPLOADING TO TELEGRAM...</b>", sts, time())
        )
    except Exception as e:
        logger.warning(f"Video upload failed, falling back to document: {e}")
        try:
            docs = await retry_on_flood(Bot.send_document)(
                chat_id=int(user_id),
                document=dl_location,
                caption=caption,
                file_name=new_filename,
                progress=progress_for_pyrogram,
                progress_args=("<b>⚡️ UPLOADING DOCUMENT...</b>", sts, time())
            )
        except Exception as fallback_e:
            logger.error(f"Fallback upload failed: {fallback_e}")

    if docs:
        # Track the video message in the user's bot chat for the 6-Hour Auto-Delete Engine
        await track_message(docs.chat.id, docs.id)

        # RESTORED: Personal Dump Channel Forwarder
        # If the user has a dump channel set, the bot copies the file there. 
        # The auto-delete engine WILL NOT delete the copy in their private dump!
        dump_channel = uts.get(user_id, {}).get('setting', {}).get('dump')
        if dump_channel:
            try: 
                await retry_on_flood(docs.copy)(int(dump_channel))
            except Exception as e: 
                logger.warning(f"Failed to forward to user dump channel: {e}")

    if Vars.LOG_CHANNEL != 0:
        log_caption = f"<blockquote><b>✲『SCANIME』✲ DELIVERY LOG</b></blockquote>\n\n<b>User:</b> <code>{user_id}</code>\n<b>File:</b> <code>{new_filename}</code>"
        try:
            await retry_on_flood(docs.copy)(Vars.LOG_CHANNEL, caption=log_caption)
        except Exception:
            pass

    if os.path.exists(dl_location):
        try: os.remove(dl_location)
        except: pass
