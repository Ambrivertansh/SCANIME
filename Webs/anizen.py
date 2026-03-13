
from bs4 import BeautifulSoup
from .base import AnimeCard, EpisodeCard, fetch_url  # Use same base import
from Tools.logger import get_logger

from urllib.parse import quote

import base64
import re


from Tools.bypasser import process_megacloud_link, decrypt_multicloud_url, process_zephyrflick_link


log = get_logger(__name__)



MSG_FORMAT = """
<b>{name} | {eng_name}


Aired: {aired}
Premiered: {premiered}
Status: {status}
MAL Score: {rate}
Genres: {genres}
Studios: {studios}

Summary: {description}

Site Url: {url}</b>"""

SIMPLE_MSG_FORMAT = """
<b>{name} | {eng_name}


Aired: {aired}
Status: {status}
Genres: {genres}

Summary: {description}

Site Url: {url}</b>"""


WATCH_API = "https://api.slay-knight.xyz/api/servers/{anime_id}"

HEADERS = {
    "Host": "anizen.tr",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
}

site_secret_key = base64.b64decode("emVuLWVuY3g=").decode('utf-8')  # "zen-encx"


def parse_quality(audio_type: str, subtitle_str = None):
    """Extract quality number from string"""
    return f"1080p [{subtitle_str}] [{audio_type}]" if subtitle_str else f"1080p [{audio_type}]"


class AnizenWebs:
    __slots__ = ('name', 'sf', 'base_url')

    def __init__(self):
        self.name = "Anizen"
        self.sf = "AZ"
        self.base_url = "https://anizen.tr"

    async def search(self, query: str):
        search_api = f"https://anizen.tr/src/ajax/anime/search-ajax.php?keyword={quote(query)}"
        json_data = await fetch_url(search_api, headers=HEADERS, return_json=True)
        results = []

        if not isinstance(json_data, dict):
            return []
        
        try:
            if "results" not in json_data and "data" not in json_data["results"]:
                return []
            
            for anime_data in json_data["results"]["data"]:
                results.append(
                    AnimeCard( #https://anizen.tr/details/one-piece-100
                        url=f"https://anizen.tr/details/{anime_data['id']}",
                        title=anime_data.get('title'),
                        poster=anime_data.get('poster', ''),
                        data=anime_data,
                        web_data=self.sf,
                    )
                )
                
        
        except Exception:
            pass
        
        return results

    async def get_info(self, animeclass: AnimeCard):
        try:
            html = await fetch_url(animeclass.url, headers=HEADERS)
            if not html:
                return animeclass
            
            bs = BeautifulSoup(html, "html.parser")
            info_div = bs.select_one("div.anisc-info")
            if not info_div:
                return animeclass

            # -- Anilist ID --
            anilist_id = bs.find(class_="anis-cover")
            anilist_id = anilist_id.get("data-anilist-id", "") if anilist_id else ""
            animeclass.data = {"anilist_id": anilist_id}

            # -- Info Data --
            description = ""
            aired = ""
            eng_name = ""
            premiered = ""
            status = ""
            rate = ""
            genres = ""
            studios = ""
            for i in info_div.find_all("div"):
                if type_msg := i.find("span", class_="item-head"):
                    label = type_msg.text.strip()
                    
                    if label == "Overview:":
                        description = i.find_next('div', class_="text")
                        description = description.text.strip() if description else ""
                        
                    elif label == "Aired:":
                        aired = i.find_next("span", class_="name")
                        aired = aired.text.strip() if aired else ""
                        
                    elif label == "Japanese:":
                        eng_name = i.find_next("span", class_="name")
                        eng_name = eng_name.text.strip() if eng_name else ""
                        
                    elif label == "Premiered:":
                        premiered = i.find_next("span", class_="name")
                        premiered = premiered.text.strip() if premiered else ""
                        
                    elif label == "Status:":
                        status = i.find_next("span", class_="name")
                        status = status.text.strip() if status else ""
                    
                    elif label == "MAL Score:":
                        rate = i.find_next("span", class_="name")
                        rate = rate.text.strip() if rate else ""
                    
                    elif label == "Genres:":
                        genres = i.find_all("a")
                        genres = ", ".join([j.text.strip() for j in genres]) if genres else ""
                    
                    elif label == "Studios:":
                        studios = i.find_next("a", class_="name")
                        studios = studios.text.strip() if studios else ""
            
            animeclass.msg = MSG_FORMAT.format(
                name=animeclass.title,
                eng_name=eng_name,
                aired=aired,
                premiered=premiered,
                status=status,
                rate=rate,
                genres=genres,
                studios=studios,
                description=description[:400],
                url=animeclass.url
            )
            if len(animeclass.msg) > 1024:
                animeclass.msg = SIMPLE_MSG_FORMAT.format(
                    name=animeclass.title,
                    eng_name=eng_name,
                    aired=aired,
                    status=status,
                    genres=genres,
                    description=description[:400],
                    url=animeclass.url
                )
                
        except Exception:
            pass
        
        return animeclass
        

    async def get_episodes(self, animeclass: AnimeCard, page: int = 1):
        try:
            request_url = animeclass.url.replace("/details/", "/watch/")
            request_url += "?ep=1"
            
            anime_id = animeclass.url.split("/")[-1]
            animeclass.data.update(
                {"anime_id": anime_id}
            )
            
            html = await fetch_url(request_url, headers=HEADERS)
            bs = BeautifulSoup(html, "html.parser")
            
            # -- Episode Data --
            episode_div = bs.select_one("div.detail-infor-content")
            episode_list = episode_div.find_all("a") if episode_div else []
            episode_list = list(reversed(episode_list))
            for episode in episode_list:
                episode_params = episode.get("data-id", "")
                if not episode_params:
                    continue
                
                episode_num = episode.get("data-number")

                
                yield EpisodeCard(
                    url=f"{self.base_url}/watch/{episode_params}",
                    title=str(episode_num), # need this for something else
                    anime_title=animeclass.title,
                    data=animeclass.data
                )
            
        except Exception as e:
            log.debug(f"[Anizen] get_episodes error: {e}")
            

    async def get_downloading_links(self, episodeclass: EpisodeCard):
        episodeclass.download_links = []
        headers = HEADERS.copy()
        headers["Host"] = "api.slay-knight.xyz"
        try:
            anime_id = episodeclass.data.get("anime_id")
            request_url = WATCH_API.format(anime_id=anime_id)
            
            anilist_id = episodeclass.data.get("anilist_id", "")
            
            ep_id = episodeclass.url.split("?ep=")[-1]
            params = {
                "ep": ep_id,
                "episode": str(episodeclass.title),
                "stream": "true"
            }
            if anilist_id:
                params["anilist_id"] = anilist_id
            
            json_data = await fetch_url(request_url, params=params, headers=headers, return_json=True)
            
            if not isinstance(json_data, dict):
                return
            
            if "result" not in json_data and "servers" not in json_data['results']:
                return

            
            for server in json_data['results']['servers']:
                api_url = None
                try:
                    server_name = server['serverName']
                    if server_name == "Mega ooo":
                        mega_url = await self.extract_mega_link(
                            episodeclass.url, server['type'], episodeclass.title, 
                            anilist_id
                        )
                        
                        tracks, sources = await process_megacloud_link(mega_url) if mega_url else (None, None)
                        source_url = sources[0].get("url") if sources else None
                        for track in tracks:
                            server_name = parse_quality(server['type'], track.get('label', ''))
                            episodeclass.download_links.append({
                                "quality": server_name,
                                "link": source_url,
                                "subtitle_link": track.get("file")
                            })
                        
                    elif server_name == "Dou" and anilist_id:
                        api_url = f"https://slay-knight.xyz/player/{anilist_id}/{episodeclass.title}/{server['type']}"
                        server_name = parse_quality(server['type'])
                    
                    elif "MultiCloud" == server_name:
                        if (decoder_url := decrypt_multicloud_url(
                            server['iframes'][0].get('src'),
                            site_secret_key=site_secret_key,
                        )):
                            dl_data = await process_zephyrflick_link(decoder_url)
                            
                            if not isinstance(dl_data, dict):
                                continue
                            
                            audios = dl_data.get("audio", [])
                            qualities = dl_data.get("qualities", [])
                            downloading_links = [
                                {
                                    "quality": server_name,
                                    "link": decoder_url,
                                    #"video_link": dl_data.get("video_link"),
                                    "video_format": f"{quality}+audio-{audio}",
                                    "audio": audio,
                                }
                                for audio in audios
                                for quality in qualities
                                if (server_name := f"{quality} [{audio}]")
                            ]
                            
                            episodeclass.download_links.extend(downloading_links)
                    
                    if api_url:
                        episodeclass.download_links.append({
                            "quality": server_name,
                            "link": api_url
                        })
                except Exception:
                    pass
            
                
        except Exception as e:
            log.error(f"[Anizen] get_downloading_links error: {e}")
    
    @staticmethod
    async def extract_mega_link(
        url, audio_type: str, episode_num: str,
        anilist_id: str, 
    ):
        """https://anizen.tr/src/player/sub.php?id=one-piece-100?ep=2142&server=Mega&embed=true&ep=1&malId=21&anilistId=21&skip=true"""
        try:
            api_url = f"https://anizen.tr/src/player/{audio_type}.php"
            url_id = url.split("/")[-1]
            params = {
                "id": quote(url_id),
                "server": "Mega",
                "embed": "true",
                "ep": str(episode_num),
                "anilistId": anilist_id,
                "skip": "true"
            }
            html = await fetch_url(api_url, params=params, headers=HEADERS)
            pattern = re.compile(r'<iframe[^>]*src="([^"]+)"')
            match = pattern.search(html)
            return match.group(1) if match else None
            
        except Exception:
            log.debug(" Got Error While Extracting Mega Link ")
        
    
