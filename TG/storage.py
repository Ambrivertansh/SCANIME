from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters

from Webs import web_data

import pyrogram.errors
import re
from bot import Vars
from Tools.logger import get_logger
from Tools.base import Queue, retry_on_flood


logger = get_logger(__name__)

search_cache = {}
back_cache = {}



def split_list(li, li_len: int = 2):
    return [li[x:x + li_len] for x in range(0, len(li), li_len)]


def iterate_list(li: list, li_len: int, page: int = 1):
    return li[(page - 1) * li_len:page * li_len] if page != 1 else li[:li_len]


def dynamic_data_filter(data):

    async def func(flt, _, query):
        return flt.data == query.data

    return filters.create(func, data=data)


def is_auth_query():

    async def func(flt, _, query):
        reply = query.message.reply_to_message
        if not reply:
            return True
        
        if not reply.from_user:
            return False

        user_id = reply.from_user.id
        query_user_id = query.from_user.id

        if user_id != query_user_id:
            await query.answer("This is not for you", show_alert=True)
            return False
        return True

    return filters.create(func)


def igrone_error(func):

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except:
            pass

    return wrapper


async def check_get_web(url):
    for web in web_data.values():
        try:
            if url.startswith(web.base_url):
                return web
        except Exception:
            pass


def plugins_list(type=None, page=1):
    button = split_list([
        InlineKeyboardButton(i, callback_data=f"plugin_{web_data[i].sf}")
        for i in web_data
    ])

    button.append([
        InlineKeyboardButton("♞ All Search ♞", callback_data="plugin_all"),
        InlineKeyboardButton("🔥 Close 🔥", callback_data="kclose")
    ])

    return InlineKeyboardMarkup(button)


async def get_webs(sf):
    return next((web for web in web_data.values() if web.sf == sf), None)





async def check_fsb(client, message):
    channel_button = []

    for channel_info in client.FSB:
        try:
            channel = int(channel_info[1])
        except:
            channel = channel_info[1]

        try:
            await client.get_chat_member(channel, message.from_user.id)
        except pyrogram.errors.UserNotParticipant:
            channel_link = channel_info[2] if len(channel_info) > 2 else (
                await client.export_chat_invite_link(channel) if isinstance(
                    channel,
                    int) else f"https://telegram.me/{channel.strip()}")
            channel_button.append(
                InlineKeyboardButton(channel_info[0], url=channel_link))
        except (pyrogram.errors.UsernameNotOccupied,
                pyrogram.errors.ChatAdminRequired) as e:
            await retry_on_flood(client.send_message)(
                Vars.LOG_CHANNEL,
                f"Channel issue: {channel} - {type(e).__name__}")
        except (pyrogram.ContinuePropagation, pyrogram.StopPropagation):
            raise
        except Exception as e:
            await retry_on_flood(client.send_message
                                 )(Vars.LOG_CHANNEL,
                                   f"Force Subscribe error: {e} at {channel}")

    return channel_button, []






def get_quality_num(data, type: str = "0"):
    pattern = re.compile(r"\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b",
                         re.IGNORECASE)
    match = re.search(pattern, data)
    if match:
        quality = match.group(1) or match.group(2)
        if type == "0":
            return quality
        elif not quality.startswith(type):
            return None
        else:
            return quality


def get_episode_number(text):
    """Extract episode/chapter number from text"""
    patterns = [
        r"Chapter\s+(\d+(?:\.\d+)?)",
        r"Volume\s+(\d+) Chapter\s+(\d+(?:\.\d+)?)",
        r"Chapter\s+(\d+)\s+-\s+(\d+(?:\.\d+)?)", r"(\d+(?:\.\d+)?)"
    ]

    text = str(text)
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1) if match.lastindex == 1 else match.group(2)
    return None
