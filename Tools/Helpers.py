from PIL import Image
import math
import time
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from os import cpu_count
import os
import json
import shutil
from urllib.parse import urlparse
import yt_dlp as youtube_dl
from Tools.logger import get_logger
from typing import Optional
from aiohttp import ClientSession 
from cloudscraper import create_scraper
import aiofiles
import re
from .base import retry_on_flood
import copy

logger = get_logger(__name__)

# 100% Branded Premium Progress Bar (No External Links)
PROGRESS_BAR = """<b>\n
╭━━━❰ ✲『SCANIME』✲ ❱━━━➣
┣⪼ 🗃️ Sɪᴢᴇ: {1} | {2}
┣⪼ ⏳️ Dᴏɴᴇ: {0}%
┣⪼ 🚀 Sᴩᴇᴇᴅ: {3}/s
┣⪼ ⏰️ Eᴛᴀ: {4}
┣⪼ 🪭 Mᴏᴅᴇ: {5}
╰━━━━━━━━━━━━━━━━━━➣ </b>"""

_scraper = create_scraper(browser='chrome')

def get_headers():
    return copy.deepcopy({
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Connection": "keep-alive",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-GPC": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    })

def get_kiwi_h():
    return copy.deepcopy({
        "Accept": "*/*", 
        "Accept-Language": "en-GB,en;q=0.9", 
        "Connection": "keep-alive", 
        "Origin": "https://kwik.cx", 
        "Referer": "https://kwik.cx/", 
        "Sec-Fetch-Dest": "video", 
        "Sec-Fetch-Mode": "cors", 
        "Sec-Fetch-Site": "cross-site", 
        "Sec-GPC": "1", 
        "Sec-Ch-Ua": '"Chromium";v="137", "Not/A)Brand";v="24"', 
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

def get_random_folder_name(base_folder= "Downloads") -> str:
    while True:
        id_ = os.urandom(13).hex()
        if not os.path.exists(f"{base_folder}/{id_}"):
            return f"{base_folder}/{id_}"

async def progress_for_pyrogram(
    current, total, ud_type, 
    message, start, file_name: str = "",
    mode: str = "Premium"
):
    now = time.time()
    diff = now - start
    try: 
        current = int(current)
    except Exception:
        if file_name and os.path.exists(file_name):
            current = os.path.getsize(file_name)

    try:
        total = int(total)
    except Exception:
        if file_name and os.path.exists(file_name):
             total = os.path.getsize(file_name)
    
    if round(diff % 10.00) == 0 or current == total:        
        percentage = current * 100 / total if total > 0 else 0
        speed = current / diff if diff > 0 else 0
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000 if speed > 0 else 0
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}{1}".format(
            ''.join(["⬢" for i in range(math.floor(percentage / 5))]),
            ''.join(["⬡" for i in range(20 - math.floor(percentage / 5))])
        )           
        tmp = progress + PROGRESS_BAR.format( 
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),            
            estimated_total_time if estimated_total_time != '' else "0 s",
            mode,
        )
        try:
            # Minimalist Text Update, Removed Wizard_Bots Button
            await message.edit_text(text=f"<code>{ud_type}</code>\n\n{tmp}")
        except Exception:
            pass

class Downloader:
    __slots__ = (
        "message", "file_name", "folder", "total_size", "full_path",
        "start_time", "current", "stop_progress", "mode"
    )
    
    def __init__(self, message, file_name, folder="Downloads"):
        self.message = message
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', file_name)
        self.folder = os.path.join(os.getcwd(), folder)
        os.makedirs(self.folder, exist_ok=True)
        self.full_path = os.path.join(self.folder, safe_filename)
        self.file_name = safe_filename
        self.total_size = 0
        self.start_time = time.time()
        self.current = 0
        self.mode = ""
        self.stop_progress = asyncio.Event()
    
    async def _update_progress(self):
        await progress_for_pyrogram(
            self.current, self.total_size, "<b>⚡️ EXTRACTING DATA...</b>", 
            self.message, self.start_time, self.full_path, self.mode,
        )
            
    async def _update_progress_loop(self):
        last_update_time = 0
        update_interval = 2 
        while not self.stop_progress.is_set():
            try:
                current_time = time.time()
                if current_time - last_update_time >= update_interval:
                    await self._update_progress()
                    last_update_time = current_time
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(3)
    
    async def download(
        self, url: str, aria2c_use: bool = True, video_format: str = "",
        headers: dict = get_headers(), direct_use: bool = False,
        cloudscraper_use: bool = False, ffmpeg_need: bool = False,
    ):
        error_came = None
        os.makedirs(self.folder, exist_ok=True)
        
        if url.startswith("https://play.zephyrflick.top/"):
            headers['Referer'] = "https://play.zephyrflick.top/"
            if 'Host' in headers: del headers['Host']
        
        # Bypasser dependency completely removed here. Direct extraction only.
        
        if "uwucdn.top/" in url:
            parsed = urlparse(url)
            headers = get_kiwi_h()
            headers['Host'] = parsed.netloc
        elif ".kwik.cx/" in url:
            headers = get_kiwi_h()
        if url.startswith("https://hlsx3cdn.echovideo.to"):
            ffmpeg_need = True
            headers['Host'] = "hlsx3cdn.echovideo.to"
            headers['Referer'] = "https://slay-knight.xyz/"
        
        progress_tasks = asyncio.create_task(self._update_progress_loop()) if self.message else None
        try:
            if direct_use:
                await self.download_with_aio(url, headers)
            elif cloudscraper_use:
                await asyncio.to_thread(lambda: self.download_with_cloudscraper(url, headers))
            else:
                await asyncio.to_thread(lambda: self.download_yt(
                    url, aria2c_use=aria2c_use, video_format=video_format, 
                    headers=headers, ffmpeg_need=ffmpeg_need,
                ))
        except Exception:
            logger.info("Retrying With Cloudscraper")
            await self.clean_folder()
            try:
                await asyncio.to_thread(self.download_with_cloudscraper, url, headers)
            except Exception as e:
                await self.clean_folder()
                error_came = e
        
        self.stop_progress.set()
        if progress_tasks and not progress_tasks.done():
            progress_tasks.cancel()
        
        files = self._find_downloaded_files()
        if error_came: raise error_came
        return files
        
    def _get_format_selector(self, video_format: str) -> str:
        format_map = {
            "480p": "best[height<=480][vcodec!=av01]/best[height<=480]/best",
            "720p": "best[height<=720][vcodec!=av01]/best[height<=720]/best", 
            "1080p": "best[height<=1080][vcodec!=av01]/best[height<=1080]/best",
            "": "best[vcodec!=av01]/best"
        }
        return format_map.get(video_format, "best[vcodec!=av01]/best")
    
    def get_info_yt(self, url):
        ydl_opts = self.get_ytdlp_headers()
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                filename = ydl.prepare_filename(info_dict)
                return info_dict, filename
        except Exception:
            return None, None

    async def download_with_aio(self, url, headers):
        self.mode = "Direct"
        os.makedirs(self.folder, exist_ok=True)
        async with ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200: raise Exception(f"HTTP error: {response.status}")
                self.total_size = int(response.headers.get('content-length', 0))
                chunk_size = 1024 * 1024
                async with aiofiles.open(self.full_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if chunk:
                            await f.write(chunk)
                            self.current += len(chunk)

    def download_with_cloudscraper(self, url, headers):
        self.mode = "Cloud"
        os.makedirs(self.folder, exist_ok=True)
        with _scraper.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            self.total_size = int(r.headers.get('content-length', 0))
            with open(self.full_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        self.current += len(chunk)
            
    def download_yt(self, url, aria2c_use=True, video_format: str = "", headers: dict = get_headers(), ffmpeg_need: bool = False):
        self.mode = "Engine"
        os.makedirs(self.folder, exist_ok=True)
        try:
            ydl_opts = self.get_ytdlp_headers()
            ydl_opts['http_headers'] = headers
            ydl_opts['format'] = self._get_format_selector(video_format)
            ydl_opts['merge_output_format'] = 'mp4'
            
            if aria2c_use: ydl_opts['external_downloader'] = 'aria2c'
            if ffmpeg_need:
                ydl_opts['external_downloader'] = 'ffmpeg'
                ydl_opts['external_downloader_args'] = ['-headers', ''.join(f'{k}: {v}\r\n' for k, v in headers.items())]
                ydl_opts['hls_use_mpegts'] = True

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
        except Exception as e:
            if "aria2c" in str(e) or "Unable to open fragment" in str(e):
                return self.download_yt(url, False, video_format, headers, ffmpeg_need)
            raise
    
    def _find_downloaded_files(self):
        all_files = []
        for root, dirs, files in os.walk(self.folder):
            for file in files:
                if not file.endswith(".mp4.part.frag.urls"):
                    all_files.append(os.path.join(root, file))
        return all_files
    
    def my_hook(self, d: dict = {}):
        if not d: return ""
        try:
            if 'fragment_index' in d and 'fragment_count' in d:
                self.total_size = d.get('_total_bytes_estimate_str', d.get('_total_bytes_str', 0))
            elif '_percent_str' in d:
                self.total_size = d.get('_total_bytes_str', 0)
            else:
                self.total_size = d.get('total_bytes', d.get('total_bytes_estimate', 0))
            self.current = d.get('downloaded_bytes', 0)
        except Exception: pass
        
    async def clean_folder(self):
        try:
            await asyncio.to_thread(lambda: shutil.rmtree(self.folder, ignore_errors=True))
        except Exception: pass

    def get_ytdlp_headers(self):
        return copy.deepcopy({
            'outtmpl': self.full_path, 
            'no_warnings': True,
            "cookiefile": "yt_cookies.txt",
            'max_filesize': 1.5 * 1024 * 1024 * 1024,  # RENDER RAM GUARD: Max 1.5GB
            "retries": 10,
            "nocheckcertificate": True,
            'progress_hooks': [self.my_hook],
        })

async def get_media_details(path: str):
    try:
        cmds = ["ffprobe", "-hide_banner", "-loglevel", "error", "-print_format", "json", "-show_format", "-show_streams", path]
        process = await asyncio.create_subprocess_exec(*cmds, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode != 0: return None, None, None
        media_info = json.loads(stdout.decode())
        video_stream = next((s for s in media_info.get("streams", []) if s.get("codec_type") == "video"), None)
        duration_str = media_info.get("format", {}).get("duration")
        if not duration_str and video_stream: duration_str = video_stream.get("duration")
        duration = float(duration_str) if duration_str else None
        return (int(video_stream["width"]) if video_stream and "width" in video_stream else None, 
                int(video_stream["height"]) if video_stream and "height" in video_stream else None, duration)
    except Exception:
        return None, None, None

async def get_stream_duration(file):
    try:
        output = f"{file}-th.jpg"
        cmd = f'''ffmpeg -hide_banner -loglevel error -ss 2 -i """{file}""" -vf thumbnail -q:v 1 -frames:v 1 -threads 1 {output} -y'''
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        return output if os.path.isfile(output) else None, None
    except Exception as er:
        return None, er

def encode(num):
    base36 = ''
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    while num > 0:
        num, rem = divmod(num, 36)
        base36 = alphabet[rem] + base36
    return base36.zfill(6)

def decode(encoded_str):
    encoded_str = encoded_str.lstrip('0')
    if not encoded_str: return 0
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    num = 0
    for char in encoded_str: num = num * 36 + alphabet.index(char)
    return num

def humanbytes(size):    
    if not size: return ""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "ᴅ, ") if days else "") + ((str(hours) + "ʜ, ") if hours else "") + ((str(minutes) + "ᴍ, ") if minutes else "") + ((str(seconds) + "ꜱ, ") if seconds else "") + ((str(milliseconds) + "ᴍꜱ, ") if milliseconds else "")
    return tmp[:-2] 

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

async def get_dimensions(path):
    image = Image.open(path)
    width, height = image.size
    return width, height
