PICS = (
    "https://spiritcat122.github.io/Images/p/14822.jpg",
    "https://spiritcat122.github.io/Images/p/14832.jpg",
    "https://spiritcat122.github.io/Images/p/16935.png",
    "https://spiritcat122.github.io/Images/p/19707529050667fbd4b3b22e0044fcd2.jpg",
    "https://spiritcat122.github.io/Images/p/24252.webp",
    "https://spiritcat122.github.io/Images/p/406dcfbd66f2eba1fdd642632c64ea26.jpeg",
    "https://spiritcat122.github.io/Images/p/4f5d5764-3ee2-499c-8e03-ece55ea51e05-blue-exorcist-wallpaper.webp",
    "https://spiritcat122.github.io/Images/p/6d36a24ba86063c5ea9c13b216e5d080.jpg",
    "https://spiritcat122.github.io/Images/p/753046-4k-ultra-hd-one-piece-wallpaper-and-background-image.jpg",
    "https://spiritcat122.github.io/Images/p/7830f5da-0100-4172-bf5f-aa7f94716c71-anime-background.webp",
    "https://spiritcat122.github.io/Images/p/986f9ff7e262b9d57f4256c7a5a0b838.jpeg",
    "https://spiritcat122.github.io/Images/p/GrszpcQXoAAtyUk.jpg",
    "https://spiritcat122.github.io/Images/p/alone-anime-guy-with-umbrella-under-the-water-city-wallpaper-1280x720_45.jpg",
    "https://spiritcat122.github.io/Images/p/anime-eyes-illustration_23-2151660526.jpg",
    "https://spiritcat122.github.io/Images/p/anime-scenery-sitting-4k-hs-1920x1080.jpg",
    "https://spiritcat122.github.io/Images/p/b1BfOn.jpg",
    "https://spiritcat122.github.io/Images/p/dI-PlrAnrf2X70rq6LxiFsboPA4hzS-2Zp4--llgH2c.webp",
    "https://spiritcat122.github.io/Images/p/download.jpeg",
    "https://spiritcat122.github.io/Images/p/guts-manga-berserk-5k-uk.jpg",
    "https://spiritcat122.github.io/Images/p/johan_liebert_minimalist__monster__by_earthlurker_db6gruz-fullview.png",
    "https://spiritcat122.github.io/Images/p/keyakizaka46-wallpaper-1280x768_13.jpg",
    "https://spiritcat122.github.io/Images/p/makima-from-chainsaw-man-4k-hl.jpg",
    "https://spiritcat122.github.io/Images/p/new-desktop-wallpaper-i-just-love-hild-so-much-v0-pr51ftkjbv9c1.webp",
    "https://spiritcat122.github.io/Images/p/one-piece-nico-robin-epic-desktop-wallpaper-preview.jpg",
    "https://ik.imagekit.io/jbxs2z512/samurai-hd-wallpap.png?updatedAt=1760517212353",
    "https://spiritcat122.github.io/Images/p/samurai-on-horseback-landscape-desktop-wallpaper-preview.jpg",
    "https://spiritcat122.github.io/Images/p/satoru-gojo-red-reversal-jujutsu-kaisen-9166.jpg",
    "https://ik.imagekit.io/jbxs2z512/zzz-1-4-banners-miyabi-harumasa.jpg_width=1200&height=900&fit=crop&quality=100&format=png&enable=upscale&auto=webp?updatedAt=1760517596231",
    "https://ik.imagekit.io/jbxs2z512/thumb-1920-1371019.png",
    "https://ik.imagekit.io/jbxs2z512/sb1ybl6cxf4b1.png?updatedAt=1760517673506",
    "https://ik.imagekit.io/jbxs2z512/e99cc5906da542ac599442b29bae4c8e.jpg?updatedAt=1760517929037",
    "https://ik.imagekit.io/jbxs2z512/7e1f4bcfec6be57c87e942c601b5271e.jpg?updatedAt=1760517959267",
    "https://ik.imagekit.io/jbxs2z512/a8dc6f1ff50cf0569297b875f601cb16.jpg?updatedAt=1760517993653",
    "https://ik.imagekit.io/jbxs2z512/01_648c4ba8-9d85-4e51-b332-22afbb9b05bb.jpg_v=1750670418?updatedAt=1760518085669",
    "https://ik.imagekit.io/jbxs2z512/vivian-wallpaper_8803af5f-cb42-4a6b-8e8a-db03142ef67d.jpg_v=1750671646?updatedAt=1760518112679",
    "https://ik.imagekit.io/jbxs2z512/08_b44d65b0-12ee-4aed-bab7-f7270aa9dcc9.jpg_v=1750670790?updatedAt=1760518142703",
    "https://ik.imagekit.io/jbxs2z512/Vivians-kit-coninues-the-off-field-attacks-in-ZZZ.jpg?updatedAt=1760518176568",
    "https://ik.imagekit.io/jbxs2z512/GpgedBkWkAAyKPU_format=jpg&name=4096x4096?updatedAt=1760518212517",
    "https://ik.imagekit.io/jbxs2z512/06_7445c21b-c17b-462f-a381-a1081483bdec.jpg_v=1750670790?updatedAt=1760518255243",
    "https://ik.imagekit.io/jbxs2z512/05_f9d4355c-5a73-4c13-a994-74ff8a0b6199.jpg_v=1750670460?updatedAt=1760518285743",
    "https://ik.imagekit.io/jbxs2z512/bf82e8564b7b2b5d786160016234c8cf_6003966760177598255.webp_x-oss-process=image_2Fresize_2Cs_1000_2Fauto-orient_2C0_2Finterlace_2C1_2Fformat_2Cwebp_2Fquality_2Cq_70?updatedAt=1760518374448",
    "https://ik.imagekit.io/jbxs2z512/1386555.jpg?updatedAt=1760518403026"
)

import pyrogram
from time import time
from Tools.logger import get_logger

from pyrogram import idle
import random, os, shutil, asyncio

from pyrogram import utils as pyroutils
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import dataclasses
import sys

logger = get_logger(__name__)


@dataclasses.dataclass(slots=True)
class Vars:
  API_ID = int(os.environ.get("API_ID", ""))
  API_HASH = os.environ.get("API_HASH", "")

  BOT_TOKEN = os.environ.get("BOT_TOKEN", "") #
  plugins = dict(root="TG", )

  LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", ""))
  UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "")
  DB_URL = os.environ.get("DB_URL", "")

  PORT = int(os.environ.get("PORT", "5000"))
  OWNER = os.environ.get("OWNER", "Shanks_Pro")
  ADMINS = os.environ.get("ADMINS", "7225682334")
  ADMINS = [int(admin) for admin in (ADMINS).split(" ")]
  ADMINS.append(OWNER)

  IS_PRIVATE = os.environ.get("IS_PRIVATE", None)
  CONSTANT_DUMP_CHANNEL = os.environ.get("CONSTANT_DUMP_CHANNEL", None)
  WEBS_HOST = os.environ.get("WEBS_HOST", None)

  DB_NAME = "Animedb"
  PING = time()

  SHORTENER = os.environ.get("SHORTENER", None)
  SHORTENER_API = os.environ.get("SHORTENER_API", "")
  DURATION = int(os.environ.get("DURATION", "20"))

  FORCE_SUB_TEXT = os.environ.get(
      "FORCE_SUB_TEXT",
      """<b><i>❗️ You must join our channel before using this feature:</i></b>"""
  )

  FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "")

  BYPASS_TXT = os.environ.get(
      "BYPASS_TXT", """<blockquote><b>🚨 ʙʏᴘᴀss ᴅᴇᴛᴇᴄᴛᴇᴅ 🚨</b></blockquote>

<blockquote expandable><b>ʜᴏᴡ ᴍᴀɴʏ ᴛɪᴍᴇs ʜᴀᴠᴇ ɪ ᴛᴏʟᴅ ʏᴏᴜ, ᴅᴏɴ'ᴛ ᴛʀʏ ᴛᴏ ᴏᴜᴛsᴍᴀʀᴛ ʏᴏᴜʀ ᴅᴀᴅ 🥸🖕

ɴᴏᴡ ʙᴇ ᴀ ɢᴏᴏᴅ ʙᴏʏ ᴀɴᴅ sᴏʟᴠᴇ ɪᴛ ᴀɢᴀɪɴ, ᴀɴᴅ ᴛʜɪs ᴛɪᴍᴇ ᴅᴏɴ'ᴛ ɢᴇᴛ sᴍᴀʀᴛ !! 🌚💭</b></blockquote>"""
  )
  PICS = PICS


pyroutils.MIN_CHAT_ID = -99999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999


def load_fsb_vars(self):
  channel = Vars.FORCE_SUB_CHANNEL
  try:
    if "," in Vars.FORCE_SUB_CHANNEL:
      for channel_line in channel.split(","):
        self.FSB.append(
            (channel_line.split(":")[0], channel_line.split(":")[1]))
    else:
      self.FSB.append((channel.split(":")[0], channel.split(":")[1]))
  except:
    logger.error(" FORCE_SUB_CHANNEL is not set correctly! ")
    sys.exit()


class Anime_Bot(pyrogram.Client, Vars):

  def __init__(self):
    super().__init__(
        "AnimeBot",
        api_id=self.API_ID,
        api_hash=self.API_HASH,
        bot_token=self.BOT_TOKEN,
        plugins=self.plugins,
        workers=50,
    )
    self.logger = logger
    self.__version__ = pyrogram.__version__
    self.FSB = []

  async def start(self):
    await super().start()

    async def run_flask():
      cmds = ("gunicorn", "app:app")
      process = await asyncio.create_subprocess_exec(
          *cmds,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE)
      stdout, stderr = await process.communicate()

      if process.returncode != 0:
        logger.error(f"Flask app failed to start: {stderr.decode()}")

      logger.info("Webs app started successfully")

    usr_bot_me = await self.get_me()

    if os.path.exists("restart_msg.txt"):
      with open("restart_msg.txt", "r") as f:
        chat_id, message_id = f.read().split(":")
        f.close()

      try:
        await self.edit_message_text(int(chat_id), int(message_id),
                                     "<code>Restarted Successfully</code>")
      except Exception as e:
        logger.exception(e)

      os.remove("restart_msg.txt")

    if os.path.exists("Process"):
      shutil.rmtree("Process")
    if self.FORCE_SUB_CHANNEL:
      load_fsb_vars(self)

    self.logger.info("""

    ██╗    ██╗██╗███████╗ █████╗ ██████╗ ██████╗     ██████╗  ██████╗ ████████╗███████╗
    ██║    ██║██║╚══███╔╝██╔══██╗██╔══██╗██╔══██╗    ██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝
    ██║ █╗ ██║██║  ███╔╝ ███████║██████╔╝██║  ██║    ██████╔╝██║   ██║   ██║   ███████╗
    ██║███╗██║██║ ███╔╝  ██╔══██║██╔══██╗██║  ██║    ██╔══██╗██║   ██║   ██║   ╚════██║
    ╚███╔███╔╝██║███████╗██║  ██║██║  ██║██████╔╝    ██████╔╝╚██████╔╝   ██║   ███████║
     ╚══╝╚══╝ ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝     ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝

    """)
    self.username = usr_bot_me.username
    self.logger.info("Make By https://t.me/Wizard_Bots ")
    self.logger.info(
        f"Manhwa Bot Started as {usr_bot_me.first_name} | @{usr_bot_me.username}"
    )

    if self.WEBS_HOST:
      await run_flask()

    MSG = f"""<blockquote><b>🔥 SYSTEMS ONLINE. READY TO RUMBLE. 🔥

DC Mode: {usr_bot_me.dc_id}

Sleep mode deactivated. Neural cores at 100%. Feed me tasks, and watch magic happen. Let’s. Get. Dangerous.</b></blockquote>"""

    PICS = random.choice(Vars.PICS)

    button = [[
        InlineKeyboardButton(
            '*Start Now*',
            url=f"https://t.me/{usr_bot_me.username}?start=start"),
        InlineKeyboardButton("*Channel*", url="telegram.me/Wizard_Bots")
    ]]

    try:
      await self.send_photo(self.UPDATE_CHANNEL,
                            photo=PICS,
                            caption=MSG,
                            reply_markup=InlineKeyboardMarkup(button))
    except:
      pass

  async def stop(self):
    await super().stop()
    self.logger.info("Anime Bot Stopped")


Bot = Anime_Bot()
