from .base import AnimeCard, EpisodeCard, fetch_url, ClientSession
from bs4 import BeautifulSoup
from Tools.logger import get_logger
import re

log = get_logger(__name__)

MSG_FORMAT = "**{title} | {jtitle}**\n\n**ID:** `{id}`\n**Genres:** `{genres}`\n**Episodes:** `{episodes}`\n**Status:** `{status}`\n**Season:** `{season}`\n**Year:** `{year}`\n\n**Url:** {url}"


class AnimepaheWebs:
    __slots__ = ('name', 'base_url', 'headers', 'sf')

    def __init__(self):
        self.name = "Animepahe"
        self.base_url = "https://animepahe.si"
        self.sf = "AP"
        self.headers = {
            'authority': 'animepahe.si',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': '__ddg2_=;',
            'dnt': '1',
            'sec-ch-ua':
            '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'x-requested-with': 'XMLHttpRequest',
            'referer': self.base_url,
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        }

    async def search(self, query: str):
        return_results = []
        api_url = f"{self.base_url}/api"
        params = {"m": "search", "q": query}

        try:
            data = await fetch_url(api_url,
                                   return_json=True,
                                   params=params,
                                   headers=self.headers)
            results = data.get("data", []) if data else []

            for anime in results:
                if anime.get("title") and "session" in anime:
                    return_results.append(
                        AnimeCard(
                            url=f"{self.base_url}/anime/{anime['session']}",
                            title=anime["title"],
                            poster=anime.get("poster"),
                            data=anime,
                            web_data=self.sf,
                        ))
            return return_results

        except Exception as er:
            log.exception(f"{self.name} Search Error: {er}")

    async def get_info(self, animeclass: AnimeCard) -> AnimeCard:
        response = await fetch_url(animeclass.url, headers=self.headers)
        soup = BeautifulSoup(response, "html.parser")

        poster_elem = soup.find("meta", {"property": "og:image"})
        poster = poster_elem.get('content') if poster_elem else None

        tdata = soup.find(class_="anime-header")
        title = tdata.find_next(
            "span").text if tdata and tdata.find_next("span") else None
        jtitle = tdata.find_next(
            "h2").text if tdata and tdata.find_next("h2") else "N/A"

        gdata = soup.find(class_="anime-genre font-weight-bold")
        genres = [genre.text for genre in gdata.find_all("a")
                  ] if gdata else ["Shonen", "Fantasy"]

        animeclass.title = title
        animeclass.poster = poster
        animeclass.msg = MSG_FORMAT.format(
            title=title or "N/A",
            jtitle=jtitle,
            genres=', '.join(genres),
            id=animeclass.data.get("id", "N/A"),
            episodes=animeclass.data.get("episodes", "N/A"),
            status=animeclass.data.get("status", "N/A"),
            season=animeclass.data.get("season", "N/A"),
            year=animeclass.data.get("year", "N/A"),
            url=animeclass.url)

        return animeclass

    async def get_episodes(self, animeclass: AnimeCard, page: int = 1):
        session_id = animeclass.data.get("session")  # Don't pop - keep data intact
        if not session_id:
            return

        while True:
            try:
                request_url = f"{self.base_url}/api?m=release&id={session_id}&page={page}"
                response = await fetch_url(request_url,
                                           return_json=True,
                                           headers=self.headers)
                
                if not response.get("data"):
                    break

                for episode in response.get("data", []):
                    episode_title = f'{episode.get("episode", "N/A")}-{episode.get("episode2", "N/A")}' if episode.get("episode2", None) else episode.get("episode", "N/A")
                    
                    yield EpisodeCard(
                        url=
                        f"https://animepahe.si/play/{session_id}/{episode.get('session', 'N/A')}",
                        title=episode_title,
                        data=episode,
                        anime_title=animeclass.title)

                page += 1
            except Exception as er:
                log.exception(f"{self.name} Get Episodes Error: {er}")

    async def get_downloading_links(self, episodeclass: EpisodeCard):
        episodeclass.download_links = []
        try:
            response = await fetch_url(episodeclass.url, headers=self.headers)
            soup = BeautifulSoup(response, "html.parser")

            for link in soup.select(".dropdown-menu a.dropdown-item"):
                url = link.get("href")
                if url and url.startswith("https://pahe.win/"):
                    kiwi_link = await self.extract_kwik_link(url)

                    if kiwi_link:
                        download_link = await self.get_dl_link(kiwi_link)
                        if download_link:
                            episodeclass.download_links.append({
                                "quality":
                                link.text.strip(),
                                "link":
                                download_link,
                                "refer_link":
                                kiwi_link,
                            })

        except Exception as e:
            log.exception(f"{self.name} Error getting downloading links: {e}")

    # --- Bypasser (Keep as is - they're static and efficient) ---
    @staticmethod
    def step_2(s, seperator, base=10):
        mapped_range = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"
        numbers = mapped_range[0:base]
        max_iter = 0
        for index, value in enumerate(s[::-1]):
            max_iter += int(value if value.isdigit() else 0) * (seperator**
                                                                index)
        mid = ''
        while max_iter > 0:
            mid = numbers[int(max_iter % base)] + mid
            max_iter = (max_iter - (max_iter % base)) / base
        return mid or '0'

    @staticmethod
    def step_1(data, key, load, seperator):
        payload = ""
        i = 0
        seperator = int(seperator)
        load = int(load)
        while i < len(data):
            s = ""
            while data[i] != key[seperator]:
                s += data[i]
                i += 1
            for index, value in enumerate(key):
                s = s.replace(value, str(index))
            payload += chr(int(AnimepaheWebs.step_2(s, seperator, 10)) - load)
            i += 1
        matches = re.findall(
            r'action="([^\"]+)" method="POST"><input type="hidden" name="_token"\s+value="([^\"]+)',
            payload)
        return matches[0] if matches else (None, None)

    @staticmethod
    async def get_dl_link(link: str):
        async with ClientSession() as s:
            try:
                async with s.get(link) as resp:
                    text = await resp.text()
                
                matches = re.findall(
                    r'\("(\S+)",\d+,"(\S+)",(\d+),(\d+)',
                    text
                )
                if not matches:
                    return None
                
                data, key, load, seperator = matches[0]
                url, token = AnimepaheWebs.step_1(data=data,
                                                  key=key,
                                                  load=load,
                                                  seperator=seperator)

                if not url or not token:
                    return None

                async with s.post(url=url,
                                  data={"_token": token},
                                  headers={'referer': link},
                                  allow_redirects=False) as resp:
                    return resp.headers.get("location")

            except Exception as e:
                log.debug(f"DL link error: {e}"
                          )  # Use debug instead of exception for common errors
                return None

    async def extract_kwik_link(self, pahe_url: str):
        """Extract Kwik.si link from Pahe.ph page"""
        try:
            response = await fetch_url(pahe_url, use_cloudscraper=True)
            soup = BeautifulSoup(response, 'html.parser')

            # Check scripts first (most common)
            for script in soup.find_all('script', type='text/javascript'):
                match = re.search(r'https://kwik\.cx/f/[\w\d]+', script.text)
                if match:
                    return match.group(0)

            # Check iframes as fallback
            for iframe in soup.find_all('iframe'):
                match = re.search(r'https://kwik\.cx/f/[\w\d]+', str(iframe))
                if match:
                    return match.group(0)

            return None

        except Exception as e:
            log.debug(f"Kwik extraction error: {e}")
            return None
