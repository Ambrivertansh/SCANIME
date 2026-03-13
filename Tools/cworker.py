from TG.storage import Queue, igrone_error, retry_on_flood, get_quality_num

from Tools.logger import get_logger
from Tools.db import uts, ensure_user
from Tools.Helpers import Downloader, progress_for_pyrogram, get_stream_duration, get_media_details
from bot import Bot, Vars
from PIL import Image
from time import time
import os
import asyncio

logger = get_logger(__name__)

def get_random_folder_name(base_folder: str = "Downloads"):
  while True:
    folder_path = f"{base_folder}/{os.urandom(10).hex()}"
    if not os.path.exists(folder_path):
      return folder_path


async def episode_worker(woker_id):
  while True:
    try:
      data, user_id, task_id = await Queue.get()
      try:
        await asyncio.sleep(6) # to make process quite slow
        await episode_download_processer(data, user_id, task_id)
        logger.info(f"Task {task_id} done by worker {woker_id}")
      except Exception as err:
        logger.exception(err)
      finally:
        await Queue.task_done(task_id)
    except Exception as err:
      logger.exception(err)



def clean_name(txt, length=-1):
  txt = txt.replace("_", "").replace("&", "").replace(";", "")
  txt = txt.replace("None", "").replace(":", "").replace("'", "")
  txt = txt.replace("|", "").replace("*", "").replace("?", "")
  txt = txt.replace(">", "").replace("<", "").replace("`", "")
  txt = txt.replace("!", "").replace("@", "").replace("#", "")
  txt = txt.replace("$", "").replace("%", "").replace("^", "")
  txt = txt.replace("~", "").replace("+", "").replace("=", "")
  txt = txt.replace("/", "").replace("\\", "").replace("\n", "")
  txt = txt.replace(".jpg", "")
  
  if length != -1:
    txt = txt[:length]
  
  return txt

async def episode_download_processer(download_, user_id, task_id):
  user_id = str(user_id)
  await ensure_user(user_id)

  sts = download_.sts

  if not download_.download_link or download_.download_link.get('link', None) is None:
    if sts:
      await retry_on_flood(sts.edit_text)("<i> No download link found... </i>")
    return

  try:
    file_name = uts[user_id]['setting'].get("file_name", None)
    file_name_len = uts[user_id]['setting'].get("f_n_l", None)

    file_name_len = int(file_name_len) if file_name_len else None
    regex_ = uts[user_id]['setting'].get("regex", None)
    quality_ = get_quality_num(download_.quality)
    if regex_:
      download_.title = str(download_.title).zfill(int(regex_))

    if file_name:
      file_name = str(file_name).replace("{name}", clean_name(download_.anime_title, file_name_len))

      file_name = str(file_name).replace("{ep}", str(download_.title))
      if quality_:
        file_name = str(file_name).replace("{res}", str(quality_))
      else:
        file_name = str(file_name).replace("{res}", " ")

      if download_.webs_data == "AP" and ('eng' in download_.download_link['quality']):
        file_name = file_name.replace("{type}", "DUB")

      elif download_.webs_data == "AP" and ('eng' not in download_.download_link['quality']):
        file_name = file_name.replace("{type}", "SUB")

      else:
        file_name = file_name.replace("{type}", " ")
    else:
      file_name = f"{clean_name(download_.anime_title)} - {download_.title} - {get_quality_num(download_.quality) if download_.quality else ' '}.mp4"
    
    try:
      await igrone_error(sts.edit_text)(
        f"<b>Downloading {file_name}</b>\n\n<b>Task ID:</b> <code>{task_id}</code>\n<b>Link:</b> <code>{download_.download_link['link']}</code>"
      ) if sts else None

      
      yt = Downloader(message=sts, file_name=file_name, folder=get_random_folder_name())
      file_path = await yt.download(
        download_.download_link['link'],
        video_format=download_.download_link.get("video_format") if "video_format" in download_.download_link else ""
      )
      
      if not file_path:
        await yt.clean_folder()
        return
      
      await igrone_error(sts.edit_text)(
          f"<b>Downloaded {file_name}</b>\n\n<b>File Path:</b> <code>{file_path}</code>"
      ) if sts else None

      if isinstance(file_path, list):
        for file_path_ in file_path:
          await send_media(file_path_, file_name, user_id, sts, download_.download_link['link'])
      else:
        await send_media(file_path, file_name, user_id, sts, download_.download_link['link'])

      await retry_on_flood(sts.delete)() if sts else None

      await yt.clean_folder()
      if isinstance(file_path, list):
        for file_path_ in file_path:
          if os.path.exists(file_path_):
            os.remove(file_path_)
      else:
        if os.path.exists(file_path):
          os.remove(file_path)
      try:
        if os.path.exists(yt.folder):
          os.rmdir(yt.folder)
      except:
        pass

    except Exception as err:
      logger.exception(err)
      await igrone_error(sts.edit_text)(f"<b>Error:</b> <code>{err}</code>") if sts else None

  except Exception as err:
    logger.exception(err)
    await igrone_error(sts.edit_text)(f"<b>Error:</b> <code>{err}</code>")  if sts else None



async def send_media(
  dl_location, new_filename,
  user_id, sts,
  link=None
):

  user_id = str(user_id)

  caption = uts[user_id]['setting'].get('caption', None)
  if caption:
    caption = caption.replace("{}", new_filename)
  else:
    caption = f"<blockquote>{new_filename}</blockquote>"

  thumb = uts[user_id]['setting'].get('thumb', None)
  thumb_path = None

  if thumb:
    await igrone_error(sts.edit)("<blockquote>Adding Thumbnail....</blockquote>") if sts else None

    thumb_path = await Bot.download_media(thumb)
    Image.open(thumb_path).convert("RGB").save(thumb_path)
    img = Image.open(thumb_path)
    img.resize((320, 320))
    img.save(thumb_path, "JPEG")

  mode = uts[user_id]['setting'].get('mode', None)
  new_filename = f"{new_filename}.mp4" if not new_filename.endswith(".mp4") or not new_filename.endswith(".mp4") else new_filename
  
  if not mode:
    thumb_path, err = await get_stream_duration(dl_location) if not thumb_path else (thumb_path, None)
    width, height, duration = await get_media_details(dl_location)
    try:
      docs = await retry_on_flood(Bot.send_video)(
        chat_id=user_id,
        video=dl_location,
        caption=caption,
        duration=duration,
        width=width,
        height=height,
        supports_streaming=True,
        file_name=new_filename,
        progress=progress_for_pyrogram,
        progress_args=("**Upload Started...**", sts, time()),
        thumb=thumb_path,
      )
    except:
      docs = await retry_on_flood(Bot.send_video)(
        chat_id=user_id,
        video=dl_location,
        caption=caption,
        supports_streaming=True,
        file_name=new_filename,
        progress=progress_for_pyrogram,
        progress_args=("**Upload Started...**", sts, time()),
        thumb=thumb_path,
      )
  else:
    try:
      docs = await Bot.send_document(
        user_id,
        document=dl_location,
        caption=caption,
        file_name=new_filename,
        progress=progress_for_pyrogram,
        progress_args=(f"**Upload Started {new_filename} ...**", sts, time()),
        thumb=thumb_path
      )
    except:
      docs = await Bot.send_document(
        user_id,
        document=dl_location,
        caption=caption,
        file_name=new_filename,
        progress=progress_for_pyrogram,
        progress_args=(f"**Upload Started {new_filename} ...**", sts, time()),
        thumb=thumb_path
      )

  if dump_channel := uts[user_id]['setting'].get('dump', None):
    try: await retry_on_flood(docs.copy)(int(dump_channel))
    except: pass 

  user_info = await Bot.get_users(user_id)
  caption = f"<blockquote>{new_filename}</blockquote>\n\n=> {user_info.mention()}\n=> <code>{user_id}</code>\n=> {link}"

  try:
    await retry_on_flood(docs.copy)(Vars.LOG_CHANNEL, caption=caption)
  except:
    pass

  try:
    await retry_on_flood(Bot.send_sticker)(
        chat_id=Vars.LOG_CHANNEL,
        sticker=
        "CAACAgUAAxkBAAEEMvlnk2WQb9YDDw3FrFRy-xvZGwjgPQACAQMAAhfwPD-tj1bRx4epxR4E"
    )
  except:
    pass

  if thumb_path and os.path.exists(thumb_path):
    try: os.remove(thumb_path)
    except: pass

  if os.path.exists(dl_location):
    os.remove(dl_location)
