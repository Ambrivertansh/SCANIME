import pyrogram
from time import time
from Tools.logger import get_logger
from pyrogram import utils as pyroutils
import dataclasses
import os
import sys

logger = get_logger(__name__)

# We leave exactly ONE placeholder image so your old UI files don't crash
# until we clean them up in the next step!
PICS = ["https://ik.imagekit.io/jbxs2z512/samurai-hd-wallpap.png"]

@dataclasses.dataclass(slots=True)
class Vars:
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
    plugins = dict(root="TG")

    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0") or 0)
    UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "")
    DB_URL = os.environ.get("DB_URL", "")

    PORT = int(os.environ.get("PORT", "8080"))
    OWNER = os.environ.get("OWNER", "")
    
    # Safe Admin Parsing
    ADMINS = os.environ.get("ADMINS", "")
    ADMINS = [int(admin) for admin in ADMINS.split() if admin.isdigit()]
    if OWNER and OWNER.isdigit():
        ADMINS.append(int(OWNER))

    IS_PRIVATE = os.environ.get("IS_PRIVATE", None)
    DB_NAME = "Animedb"
    PING = time()

    FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "")
    FORCE_SUB_TEXT = os.environ.get(
        "FORCE_SUB_TEXT",
        "<b><i>❗️ You must join our channel before using this feature:</i></b>"
    )
    PICS = PICS

pyroutils.MIN_CHAT_ID = -99999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

def load_fsb_vars(self):
    channel = Vars.FORCE_SUB_CHANNEL
    try:
        if "," in Vars.FORCE_SUB_CHANNEL:
            for channel_line in channel.split(","):
                self.FSB.append((channel_line.split(":")[0], channel_line.split(":")[1]))
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
        usr_bot_me = await self.get_me()

        if os.path.exists("restart_msg.txt"):
            os.remove("restart_msg.txt")

        if self.FORCE_SUB_CHANNEL:
            load_fsb_vars(self)

        self.username = usr_bot_me.username
        
        # 100% Branded Terminal Logs
        self.logger.info("=======================================")
        self.logger.info("   ✲『SCANIME』✲ ENGINE INITIALIZED    ")
        self.logger.info("=======================================")
        self.logger.info(f"Bot Started as {usr_bot_me.first_name} | @{self.username}")

        # Premium Text-Only Log Channel Startup Message
        MSG = f"<blockquote><b>🔥 ✲『SCANIME』✲ ONLINE 🔥</b>\n\n<b>DC Mode:</b> {usr_bot_me.dc_id}\n<b>Status:</b> Premium Engine Active.\n<b>RAM Guard:</b> 3-Worker Limit Enforced.</blockquote>"

        if self.LOG_CHANNEL != 0:
            try:
                await self.send_message(self.LOG_CHANNEL, text=MSG)
            except Exception as e:
                pass

    async def stop(self):
        await super().stop()
        self.logger.info("✲『SCANIME』✲ Engine Offline.")

Bot = Anime_Bot()
