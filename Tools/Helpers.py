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

#from curl_cffi import AsyncSession

from aiohttp import ClientSession 
from cloudscraper import create_scraper
import aiofiles
import re

from .base import retry_on_flood
from .bypasser import bypasser_link
import copy


logger = get_logger(__name__)

PROGRESS_BAR = """<b>\n
╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣
┣⪼ 🗃️ Sɪᴢᴇ: {1} | {2}
┣⪼ ⏳️ Dᴏɴᴇ : {0}%
┣⪼ 🚀 Sᴩᴇᴇᴅ: {3}/s
┣⪼ ⏰️ Eᴛᴀ: {4}
┣⪼ 🪭 Mᴏᴅᴇ: {5}
┣⪼ 😎 @Wizard_Bots
╰━━━━━━━━━━━━━━━➣ </b>"""



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
    mode: str = "Pyro"
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
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
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
            await message.edit(
                text=f"{ud_type}\n\n{tmp}",               
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Group ✖️", url="https://t.me/WizardBotHelper")]])                                          
            )
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
        """Continuously update progress"""
        
        await progress_for_pyrogram(
            self.current, 
            self.total_size, 
            "**Downloading.....**", 
            self.message, 
            self.start_time,
            self.full_path,
            self.mode,
        )
            
    async def _update_progress_loop(self):
        last_update_time = 0
        update_interval = 1  # Update every second

        while not self.stop_progress.is_set():
            try:
                current_time = time.time()

                # Only update if enough time has passed
                if current_time - last_update_time >= update_interval:
                    await self._update_progress()
                    last_update_time = current_time

                # Short sleep to prevent CPU hogging
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            
            except Exception as e:
                await asyncio.sleep(3)
    
    async def download(
        self, url: str, 
        aria2c_use: bool = True, 
        video_format: str = "",
        headers: dict = get_headers(),
        direct_use: bool = False,
        cloudscraper_use: bool = False,
        ffmpeg_need: bool = False,
    ):
        """Main download method - ensures files are saved in the specified folder"""
        error_came = None
        os.makedirs(self.folder, exist_ok=True)
        
        if url.startswith("https://play.zephyrflick.top/"):
            headers['Referer'] = "https://play.zephyrflick.top/"
            if 'Host' in headers:
                del headers['Host']
        
        url = await bypasser_link(url) # THis Extract DIrect Downloader Link
        logger.debug(f" Url Bypass to {url}")
        
        # UWUCDN fix - dynamic Host header (t.me/nullzair)
        if "uwucdn.top/" in url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            headers = get_kiwi_h()
            headers['Host'] = parsed.netloc  # e.g., vault-05.uwucdn.top
        
        # Kwik CDN fix by t.me/nullzair
        elif ".kwik.cx/" in url:
            headers = get_kiwi_h()
        
        if url.startswith("https://hlsx3cdn.echovideo.to"):
            ffmpeg_need = True
            headers['Host'] = "hlsx3cdn.echovideo.to"
            headers['Referer'] = "https://slay-knight.xyz/"
        
        
        progress_tasks = asyncio.create_task(self._update_progress_loop()) if self.message else None # Only run if message is provided
        try:
            if direct_use:
                await self.download_with_aio(url, headers)
            elif cloudscraper_use:
                await asyncio.to_thread(lambda: self.download_with_cloudscraper(url, headers))
            else:
                await asyncio.to_thread(lambda: self.download_yt(
                    url, aria2c_use=aria2c_use, 
                    video_format=video_format, headers=headers,
                    ffmpeg_need=ffmpeg_need,
                ))
            
        except Exception:
            #await retry_on_flood(self.message.edit_text)("<b>Retrying With Cloudscraper</b>")
            logger.info("Retrying With Cloudscraper")
            await self.clean_folder()
            try:
                await asyncio.to_thread(self.download_with_cloudscraper, url, headers)
            except Exception as e:
                await self.clean_folder()
                error_came = e
        
        self.stop_progress.set()
        if progress_tasks and not progress_tasks.done():
            try:
                await asyncio.wait_for(progress_tasks, timeout=2)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                progress_tasks.cancel()
                try:
                    await progress_tasks
                except asyncio.CancelledError:
                    pass
        
        files = self._find_downloaded_files()
        logger.info(f"Downloaded files: {files}")
        if error_came:
            raise error_came
        
        return files
        
    def _get_format_selector(self, video_format: str) -> str:
        """Get appropriate format selector to avoid encryption issues"""
        format_map = {
            "480p": "best[height<=480][vcodec!=av01]/best[height<=480]/best",
            "720p": "best[height<=720][vcodec!=av01]/best[height<=720]/best", 
            "1080p": "best[height<=1080][vcodec!=av01]/best[height<=1080]/best",
            "": "best[vcodec!=av01]/best"  # Avoid AV1 codec which can cause issues
        }
        return format_map.get(video_format, "best[vcodec!=av01]/best") if video_format in format_map else video_format
    
    def get_info_yt(self, url):
        """Get video info with proper folder path"""
        ydl_opts = self.get_ytdlp_headers()
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                filename = ydl.prepare_filename(info_dict)
                
                return info_dict, filename
        except Exception:
            return None, None

    async def download_with_aio(self, url, headers):
        self.mode = "Aio"
        os.makedirs(self.folder, exist_ok=True)
        async with ClientSession() as session:
            try:
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP error: {response.status}")

                    self.total_size = int(response.headers.get('content-length', 0))

                    # Better approach: use reasonable chunk size (e.g., 1MB)
                    chunk_size = 1024 * 1024  # 1MB chunks

                    async with aiofiles.open(self.full_path, 'wb') as f:
                        # Download in chunks instead of all at once
                        async for chunk in response.content.iter_chunked(chunk_size):
                            if chunk:
                                await f.write(chunk)
                                self.current += len(chunk)

            except Exception as e:
                logger.exception(f"Download error: {e}")
                raise

    def download_with_cloudscraper(self, url, headers):
        self.mode = "Cloudscraper"
        os.makedirs(self.folder, exist_ok=True)
        with _scraper.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            self.total_size = int(r.headers.get('content-length', 0))
            with open(self.full_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        self.current += len(chunk)
            
            
    def download_yt(
        self, url, aria2c_use=True, 
        video_format: str = "", 
        headers: dict = get_headers(),
        ffmpeg_need: bool = False,
    ):
        """Download with yt-dlp - FIXED to always use folder"""
        self.mode = "Yt-dlp"
        os.makedirs(self.folder, exist_ok=True)
        try:
            ydl_opts = self.get_ytdlp_headers()
            ydl_opts['http_headers'] = headers
            
            format_selector = self._get_format_selector(video_format)
            ydl_opts['format'] = format_selector
            
            ydl_opts['merge_output_format'] = 'mp4'
            
            info, full_path = self.get_info_yt(url)
            
            
            if aria2c_use is True:
                ydl_opts['external_downloader'] = 'aria2c'
            
            if ffmpeg_need is True:
                ydl_opts['external_downloader'] = 'ffmpeg'
                ydl_opts['external_downloader_args'] = ['-headers', ''.join(f'{k}: {v}\r\n' for k, v in headers.items())]
                ydl_opts['hls_use_mpegts'] = True
                
            
            logger.error(headers)
            logger.error(ydl_opts)
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
        except Exception as e:
            if "aria2c" in str(e): # if aria2c give error then download without using it
                return self.download_yt(url, False, video_format)
            elif "Unable to open fragment" in str(e):
                return self.download_yt(url, False, video_format)
            
            raise
    
    def _find_downloaded_files(self):
        """Find all files in the download folder"""
        all_files = []
        remove_part = ".mp4.part.frag.urls"
        for root, dirs, files in os.walk(self.folder):
            for file in files:
                full_path = os.path.join(root, file)
                if full_path.endswith(remove_part):
                    continue
                all_files.append(full_path)

        return all_files
    
 
    def my_hook(self, d: dict = {}):
        """Format progress information with comprehensive fragment support"""
        if not d:
            return ""
        
        try:
            if 'fragment_index' in d and 'fragment_count' in d:
                self.total_size = d.get('_total_bytes_estimate_str', d.get('_total_bytes_str', 0))
                
            elif '_percent_str' in d:
                self.total_size = d.get('_total_bytes_str', 0)
                
            else:
                self.total_size = d.get('total_bytes', d.get('total_bytes_estimate', 0))
            
            self.current = d.get('downloaded_bytes', 0)
        except Exception:
            pass
        
    
    async def clean_folder(self):
        """Clean up downloaded folder asynchronously"""
        try:
            await asyncio.to_thread(lambda: shutil.rmtree(self.folder, ignore_errors=True))
            if os.path.exists(self.folder):
                await asyncio.to_thread(lambda: os.rmdir(self.folder))
        except Exception as err:
            logger.exception(f"Failed to clean folder: {err}")
            
        return

    
    #@staticmethod
    def get_ytdlp_headers(self):
        return copy.deepcopy({
            'outtmpl': self.full_path, #os.path.join(self.folder, '%(title)s.%(ext)s'),  # FIX: Always use folder
            'no_warnings': True,
            "cookiefile": "yt_cookies.txt",
            'max_filesize': 2 * 1024 * 1024 * 1024,  # 2GB
            "retries": 10,
            "retry_sleep_functions": {
                "http": lambda n: 5,
                "fragment": lambda n: 5,
                "file_access": lambda n: 5,
                "extractor": lambda n: 5,
            },
            "allow_multiple_video_streams": True,
            "allow_multiple_audio_streams": True,
            'nocheckcertificate': True,
            'progress_hooks': [self.my_hook],
            #'quiet': True,
        })



async def get_media_details(path: str):
  """
    Get media details (width, height, duration) using ffprobe.

    Args:
        path: Path to the media file

    Returns:
        Tuple of (width, height, duration) or None if error occurs
    """
  try:
    cmds = [
        "ffprobe",
        "-hide_banner",
        "-loglevel",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        path,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmds, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
      stderr_msg = stderr.decode().strip()
      logger.error(f"FFprobe error ({process.returncode}): {stderr_msg}")
      return None, None, None

    try:
      media_info = json.loads(stdout.decode())
    except json.JSONDecodeError as e:
      logger.error(f"Failed to parse FFprobe output: {e}")
      return None, None, None

    video_stream = next((stream for stream in media_info.get("streams", [])
                         if stream.get("codec_type") == "video"), None)

    duration_str = media_info.get("format", {}).get("duration")
    if not duration_str and video_stream:
      duration_str = video_stream.get("duration")

    try:
      duration = float(duration_str) if duration_str else None
    except (TypeError, ValueError):
      duration = None

    return (int(video_stream["width"]) if video_stream
            and "width" in video_stream else None, int(video_stream["height"])
            if video_stream and "height" in video_stream else None, duration)

  except FileNotFoundError:
    logger.error("Error: ffprobe not found. Please install FFmpeg.")
    return None, None, None
  except Exception as e:
    logger.error(f"Unexpected error processing media: {e}")
    return None, None, None


async def get_stream_duration(file):
    try:
        tduration = 5//2
        output = f"{file}-th.jpg"
        
        cmd = f'''ffmpeg -hide_banner -loglevel error -ss {tduration} -i """{file}""" -vf thumbnail -q:v 1 -frames:v 1 -threads {cpu_count() // 2} {output} -y'''
        
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
    
        error = stderr.decode().strip() if stderr else "HELLO"
        
        return output if os.path.isfile(output) else None, error
    except Exception as er:
        return None, er




def encode(num):
    # Convert the integer to a base-36 string
    base36 = ''
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    
    while num > 0:
        num, rem = divmod(num, 36)
        base36 = alphabet[rem] + base36
    
    # Pad with leading zeros to ensure it's 6 characters long
    return base36.zfill(6)

def decode(encoded_str):
    # Remove leading zeros
    encoded_str = encoded_str.lstrip('0')
    
    # If the string is empty after stripping, return 0
    if not encoded_str:
        return 0
    
    # Convert the base-36 string back to an integer
    alphabet = '0123456789abcdefghijklmnopqrstuvwxyz'
    num = 0
    
    for char in encoded_str:
        num = num * 36 + alphabet.index(char)
    
    return num


def humanbytes(size):    
    if not size:
        return ""
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
    tmp = ((str(days) + "ᴅ, ") if days else "") + \
        ((str(hours) + "ʜ, ") if hours else "") + \
        ((str(minutes) + "ᴍ, ") if minutes else "") + \
        ((str(seconds) + "ꜱ, ") if seconds else "") + \
        ((str(milliseconds) + "ᴍꜱ, ") if milliseconds else "")
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
