from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .storage import *
import pyrogram.errors

from bot import Bot, Vars
from Tools.logger import get_logger

import random
from Tools.db import ensure_user, delete_user, get_all_users

import time

from asyncio import create_subprocess_exec
from os import execl
from sys import executable

import shutil, psutil, time, os, platform
import asyncio

from datetime import datetime

HELP_MSG = """
<blockquote><b>✲『SCANIME』✲ | PROTOCOL MANUAL</b></blockquote>

<b>To download an anime just type the name of the anime you want to keep up to date.</b>

For example:
<code>One Piece</code>

<blockquote expandable><i>Then you will have to choose the language. Depending on this language, you will be able to choose the website where you could download the episode. Here you will have the option to subscribe, or to choose a chapter to download. The chapters are sorted according to the website.</i></blockquote>
"""

logger = get_logger(__name__)

@Bot.on_message(filters.private)
async def on_private_message(client, message):
    
    channel = Vars.FORCE_SUB_CHANNEL
    if channel in ["None", None, "none", "OFF", False, "False", ""]:
        return message.continue_propagation()

    if not client.FSB or client.FSB == []:
        return message.continue_propagation()

    channel_button, change_data = await check_fsb(client, message)
    if not channel_button:
        return message.continue_propagation()

    channel_button = split_list(channel_button)
    channel_button.append([InlineKeyboardButton("𝗥𝗘𝗙𝗥𝗘𝗦𝗛 ⟳", callback_data="refresh")])

    await retry_on_flood(message.reply_text)(
        text=Vars.FORCE_SUB_TEXT,
        reply_markup=InlineKeyboardMarkup(channel_button),
        quote=True,
    )
    if change_data:
        for change_ in change_data:
            client.FSB[change_[0]] = (change_[1], change_[2], change_[3])

@Bot.on_message(filters.command("start"))
async def start(client, message):
    await ensure_user(message.from_user.id)
    ping = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - Vars.PING))
    
    caption = (
        "<blockquote><b>⚡️ ✲『SCANIME』✲ ENGINE ONLINE ⚡️</b></blockquote>\n\n"
        "<b><i>How to use? Just type the name of the anime you want to keep up to date.</i></b>\n\n"
        "<b><i>For example:</i></b>\n"
        "<code>One Piece</code>\n\n"
        f"<b><i>Ping:- {ping}</i></b>\n"
        "<b><i>Check /help for more information.</i></b>"
    )
    
    await message.reply_text(
        text=caption,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⌜sᴇᴛᴛɪɴɢs⌟", callback_data="main_settings"),
                InlineKeyboardButton("⌜ᴄʟᴏsᴇ⌟", callback_data="close")
            ]
        ])
    )

@Bot.on_message(filters.command(["log", "logs"]) & filters.user(Vars.ADMINS))
async def log_(_, message):
    try:
        caption = f"<b>Log File</b>\n\n<b>Date:</b> <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>"
        with open("log.txt", "rb") as log_file:
            await retry_on_flood(message.reply_document)("log.txt", caption=caption)
    except Exception as err:
        await retry_on_flood(message.reply)(f"<b>Error:</b> <code>{err}</code>")

@Bot.on_message(filters.command(["del", "delete"]) & filters.user(Vars.ADMINS))
async def del_(_, message):
    try:
        user_id = message.text.split(" ")[1]
        if user_id in Vars.ADMINS:
            Vars.ADMINS.remove(user_id)
        await retry_on_flood(message.reply)(f"<b>Deleted:</b> <code>{user_id}</code>")
        
    except Exception as err:
        await retry_on_flood(message.reply)(f"<b>Error:</b> <code>{err}</code>")

@Bot.on_message(filters.command(["add"]) & filters.user(Vars.ADMINS))
async def add_(_, message):
    try:
        user_id = message.text.split(" ")[1]
        if user_id not in Vars.ADMINS:
            Vars.ADMINS.append(user_id)
        
        await retry_on_flood(message.reply)(f"<b>Added:</b> <code>{user_id}</code>")

    except Exception as err:
        await retry_on_flood(message.reply)(f"<b>Error:</b> <code>{err}</code>")

@Bot.on_message(filters.command(["broadcast", "b"]) & filters.user(Vars.ADMINS))
async def b_handler(_, msg):
    return await borad_cast_(_, msg)

@Bot.on_message(filters.command(["pbroadcast", "pb"]) & filters.user(Vars.ADMINS))
async def pb_handler(_, msg):
    return await borad_cast_(_, msg, True)

async def borad_cast_(_, message, pin=None):
    sts = await message.reply_text("<code>Processing...</code>")
    if message.reply_to_message:
        user_ids = await get_all_users()
        msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        await retry_on_flood(sts.edit)("<code>Broadcasting...</code>")
        for user_id in user_ids:
            try:
                docs = await msg.copy(int(user_id))
                if pin:
                    await docs.pin(both_sides=True)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                docs = await msg.copy(int(user_id))
                if pin:
                    await docs.pin(both_sides=True)
                successful += 1
            except pyrogram.errors.UserIsBlocked:
                await delete_user(user_id)
                blocked += 1
            except pyrogram.errors.PeerIdInvalid:
                await delete_user(user_id)
                unsuccessful += 1
            except pyrogram.errors.InputUserDeactivated:
                await delete_user(user_id)
                deleted += 1
            except pyrogram.errors.UserNotParticipant:
                await delete_user(user_id)
                blocked += 1
            except:
                unsuccessful += 1

        status = f"""<b><u>Broadcast Completed</u>

        Total Users: <code>{total}</code>
        Successful: <code>{successful}</code>
        Blocked Users: <code>{blocked}</code>
        Deleted Accounts: <code>{deleted}</code>
        Unsuccessful: <code>{unsuccessful}</code></b>"""

        await retry_on_flood(sts.edit)(status)
    else:
        await retry_on_flood(sts.edit)("<code>Reply to a message to broadcast it.</code>")

@Bot.on_message(filters.command("restart") & filters.user(Vars.ADMINS))
async def restart_(client, message):
    msg = await message.reply_text("<code>Restarting.....</code>", quote=True)
    with open("restart_msg.txt", "w") as file:
        file.write(str(msg.chat.id) + ":" + str(msg.id))
        file.close()

    await (await create_subprocess_exec("python3", "update.py")).wait()
    execl(executable, executable, "-B", "main.py")

def humanbytes(size):
    if not size:
        return ""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def get_process_stats():
    p = psutil.Process(os.getpid())
    try:
        cpu = p.cpu_percent(interval=0.5)
    except Exception:
        cpu = "N/A"
    try:
        mem_info = p.memory_info()
        rss = humanbytes(mem_info.rss)
        vms = humanbytes(mem_info.vms)
    except Exception:
        rss = vms = "N/A"
    return (
        f" ├ CPU:  `{cpu}%`\n"
        f" ├ RAM (RSS):  `{rss}`\n"
        f" └ RAM (VMS):  `{vms}`"
    )

@Bot.on_message(filters.command('stats'))
async def show_stats(client, message):
    total_disk, used_disk, free_disk = shutil.disk_usage(".")
    total_disk_h = humanbytes(total_disk)
    used_disk_h = humanbytes(used_disk)
    free_disk_h = humanbytes(free_disk)
    disk_usage_percent = psutil.disk_usage('/').percent

    net_start = psutil.net_io_counters()
    time.sleep(2)
    net_end = psutil.net_io_counters()

    bytes_sent = net_end.bytes_sent - net_start.bytes_sent
    bytes_recv = net_end.bytes_recv - net_start.bytes_recv

    cpu_cores = os.cpu_count()
    cpu_usage = psutil.cpu_percent()

    ram = psutil.virtual_memory()
    ram_total = humanbytes(ram.total)
    ram_used = humanbytes(ram.used)
    ram_free = humanbytes(ram.available)
    ram_usage_percent = ram.percent

    try:
        uptime_seconds = time.time() - Vars.PING
        uptime = time.strftime("%Hh %Mm %Ss", time.gmtime(uptime_seconds))
    except:
        uptime = "N/A"

    start_time = time.time()
    status_msg = await message.reply('📊 **Accessing System Details...**')
    end_time = time.time()
    time_taken_ms = (end_time - start_time) * 1000

    os_name = platform.system()
    os_version = platform.release()
    python_version = platform.python_version()

    response_text = f"""
🖥️ **System Statistics Dashboard**

💾 **Disk Storage**
├ Total:  `{total_disk_h}`
├ Used:  `{used_disk_h}` ({disk_usage_percent}%)
└ Free:  `{free_disk_h}`

🧠 **RAM (Memory)**
├ Total:  `{ram_total}`
├ Used:  `{ram_used}` ({ram_usage_percent}%)
└ Free:  `{ram_free}`

⚡ **CPU**
├ Cores:  `{cpu_cores}`
└ Usage:  `{cpu_usage}%`

🔌 **Bot Process**
{get_process_stats()}

🌐 **Network**
├ Upload Speed:  `{humanbytes(bytes_sent/2)}/s`
├ Download Speed:  `{humanbytes(bytes_recv/2)}/s`
└ Total I/O:  `{humanbytes(net_end.bytes_sent + net_end.bytes_recv)}`

📟 **System Info**
├ OS:  `{os_name}`
├ OS Version:  `{os_version}`
├ Python:  `{python_version}`
└ Uptime:  `{uptime}`

⏱️ **Performance**
└ Current Ping:  `{time_taken_ms:.3f} ms`
"""

    await message.reply_text(response_text, quote=True)
    await status_msg.delete()

@Bot.on_message(filters.command("shell") & filters.user(Vars.ADMINS))
async def shell(_, message):
    cmd = message.text.split(maxsplit=1)
    if len(cmd) == 1:
        return await message.reply("<code>No command to execute was given.</code>")

    cmd = cmd[1]
    proc = await asyncio.create_subprocess_shell(cmd,
                                                 stdout=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    stdout = stdout.decode().strip()
    stderr = stderr.decode().strip()
    reply = ""
    if len(stdout) != 0:
        reply += f"<b>Stdout</b>\n<blockquote>{stdout}</blockquote>\n"
    if len(stderr) != 0:
        reply += f"<b>Stderr</b>\n<blockquote>{stderr}</blockquote>"

    if len(reply) > 3000:
        file_name = "shell_output.txt"
        with open(file_name, "w") as out_file:
            out_file.write(reply)
        await message.reply_document(file_name)
        os.remove(file_name)
    elif len(reply) != 0:
        await message.reply(reply)
    else:
        await message.reply("No Reply")

@Bot.on_message(filters.command("export") & filters.user(Vars.ADMINS))
async def export_(_, message):
    cmd = message.text.split(maxsplit=1)
    if len(cmd) == 1:
        return await message.reply("<code>File Name Not given.</code>")

    sts = await message.reply("<code>Processing...</code>")
    try:
        file_name = cmd[1]
        if "*2" in file_name:
            file_name = file_name.replace("*2", "")
            file_name = f"__{file_name}__"

        if os.path.exists(file_name):
            await message.reply_document(file_name)
            await sts.delete()
        else:
            await sts.edit("<code>File Not Found</code>")
    except Exception as err:
        await sts.edit(str(err))

@Bot.on_message(filters.command("import") & filters.user(Vars.ADMINS))
async def import_(_, message):
    cmd = message.text.split(maxsplit=1)
    if len(cmd) == 1:
        return await message.reply("<code>File Name Not given.</code>")

    sts = await message.reply("<code>Processing...</code>")
    try:
        file_name = cmd[1]
        if "*2" in file_name:
            file_name = file_name.replace("*2", "")
            file_name = f"__{file_name}__"

        if not os.path.exists(file_name):
            if message.reply_to_message and message.reply_to_message.document:
                await message.reply_to_message.download(file_name=file_name)
                await sts.edit("<code>File Imported Successfully</code>")
            else:
                await sts.edit("<code>Please reply to a document to import.</code>")
        else:
            await sts.edit("<code>File Path Already Exists</code>")
    except Exception as err:
        await sts.edit(str(err))

@Bot.on_message(filters.command(["clean", "c"]) & filters.user(Vars.ADMINS))
async def clean(_, message):
    directory = '/app'
    ex = (".mkv", ".mp4", ".zip", ".pdf", ".png", ".epub", ".temp")
    protected_dirs = (".git", "venv", "env", "__pycache__")
    sts = await message.reply_text("🔍 Cleaning files...")
    deleted_files = []
    removed_dirs = []

    if os.path.exists("Process"):
        shutil.rmtree("Process")
    elif os.path.exists("./Process"):
        shutil.rmtree("./Process")

    try:
        for root, dirs, files in os.walk(directory, topdown=False):
            dirs[:] = [d for d in dirs if d not in protected_dirs]
            for file in files:
                if file.lower().endswith(ex):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                    except Exception as e:
                        pass

                elif file.lower().startswith("vol"):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                    except Exception as e:
                        pass

            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        removed_dirs.append(dir_path)

                    elif dir_path == "/app/Downloads":
                        os.rmdir("/app/Downloads")
                        removed_dirs.append("/app/Downloads")

                    elif dir_path == "/app/downloads":
                        os.rmdir("/app/downloads")
                        removed_dirs.append("/app/downloads")

                    try:
                        dir_path = int(dir_path)
                        os.rmdir(dir_path)
                        removed_dirs.append(dir_path)
                    except:
                        pass
                except Exception as e:
                    pass

        msg = "**🧹 Cleaning Logs:**\n"
        if deleted_files:
            msg += f"🗑 **Deleted {len(deleted_files)} files:**\n" + "\n".join(
                    deleted_files[:10])
            if len(deleted_files) > 10:
                msg += f"\n...and {len(deleted_files) - 10} more."
        else:
            msg += "✅ No files deleted."

        if removed_dirs:
            msg += f"\n\n📁 **Removed {len(removed_dirs)} empty directories:**\n" + "\n".join(
                    removed_dirs[:5])
            if len(removed_dirs) > 5:
                msg += f"\n...and {len(removed_dirs) - 5} more."

        await sts.edit(msg[:4096])
    except Exception as err:
        await sts.edit(f"❌ Error: {str(err)}")

def remove_dir(path):
    try:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(path)
    except Exception as err:
        return err

@Bot.on_message(filters.command("help"))
async def help(client, message):
    if Vars.IS_PRIVATE:
        if message.chat.id not in Vars.ADMINS:
            return await message.reply("<code>Access Denied.</code>")

    return await message.reply(HELP_MSG)
