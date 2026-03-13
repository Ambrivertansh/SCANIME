from .base import AnimeCard, EpisodeCard, fetch_url, post_url
from bs4 import BeautifulSoup
from Tools.logger import get_logger
import re

log = get_logger(__name__)

MSG_FORMAT = "**{title}**\n\n**ID:** `{id}`\n**Genres:** `{genres}`\n**Lastest:** `{lastest}`\n\n**Url:** {url}"


class AnimeXinWebs:
    __slots__ = ('name', 'base_url', 'search_url', 'mirror_url', 'headers',
                 'sf')

    def __init__(self):
        self.name = "AnimeXin"
        self.sf = "AX"
        self.base_url = "https://animexin.dev"
        self.mirror_url = "https://www.mirrored.to"
        self.search_url = "https://animexin.dev/wp-admin/admin-ajax.php"
        self.headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def search(self, query: str):
        results = []
        try:
            params = {"action": "ts_ac_do_search", "ts_ac_query": query}
            data = await post_url(self.search_url,
                                  data=params,
                                  return_json=True,
                                  use_cloudscraper=True)

            # Fast flatten with generator expression
            for anime_data in (item for category in data.get('anime', [])
                               for item in category.get('all', [])):

                results.append(
                    AnimeCard(
                        url=anime_data['post_link'],
                        title=anime_data['post_title'],
                        poster=anime_data['post_image'],
                        web_data=self.sf,
                        msg=MSG_FORMAT.format(
                            title=anime_data['post_title'],
                            id=anime_data['ID'],
                            genres=anime_data.get('post_genres', 'N/A'),
                            lastest=anime_data.get('post_latest', 'N/A'),
                            url=anime_data['post_link'])
                    )
                )

            return results
        except Exception as err:
            log.debug(f"Search failed: {err}")

    async def get_info(self, animeclass: AnimeCard) -> AnimeCard:
        return animeclass

    async def get_episodes(self, animeclass: AnimeCard, page: int = 1):
        try:
            response = await fetch_url(animeclass.url,
                                       use_cloudscraper=True,
                                       headers=self.headers)
            soup = BeautifulSoup(response, "html.parser")

            # Fast single-pass parsing
            if (episode_list := soup.find(class_="eplister")):
                for card in episode_list.find_all("a"):
                    if (title_elem := card.find("div")) and title_elem.string:
                        yield EpisodeCard(url=card['href'],
                                          title=title_elem.string.strip(),
                                          data={},
                                          anime_title=animeclass.title)
        except Exception as er:
            log.debug(f"Episodes fetch failed: {er}")

    async def get_downloading_links(self, episodeclass: EpisodeCard):
        """Store links directly in episodeclass.download_links list"""
        episodeclass.download_links = []

        try:
            response = await fetch_url(
                episodeclass.url, use_cloudscraper=True,
                headers=self.headers
            )
            soup = BeautifulSoup(response, "html.parser")

            # Extract streaming link (fast walrus operator)
            if (iframe := soup.find("iframe", src=re.compile(r"dailymotion"))):
                for quality in ["360p", "720p", "1080p", "2k"]:
                    url = iframe.get("src", "")
                    if url:
                        episodeclass.download_links.append({
                            "quality": f"Server 1 [{quality}]",
                            "link": url,
                            "video_format": quality,
                        }) 
                

            # Extract download link - process only first valid
            if (download_section := soup.find(class_="mctnx")):
                for card in download_section.find_all("a", href=True):
                    href = card['href']
                    if 'mirrored.to' in href and 'eng.mp4' in href:
                        if (download_link := await self.process_mirrored_link(href)):
                            for quality in ["360p", "720p", "1080p", "2k"]:
                                episodeclass.download_links.append({
                                    "quality": f"Server 2 {quality}",
                                    "link": download_link,
                                    "video_format": quality,
                                })
                            break  # Stop after first success

        except Exception:
            log.debug("Download links failed")


    @staticmethod
    async def process_mirrored_link(link: str):
        """Ultra-fast processing with minimal operations"""
        try:
            # Step 1: Get redirect URL
            data = await fetch_url(link, use_cloudscraper=True)
            soup = BeautifulSoup(data, "html.parser")

            if not (col_element :=
                    soup.find(class_="col-sm centered extra-top")):
                return None
            if not (redirect_url := col_element.find("a")['href']):
                return None

            # Step 2: Extract AJAX URL
            data = await fetch_url(redirect_url, use_cloudscraper=True)
            soup = BeautifulSoup(data, "html.parser")

            # Fast regex search in script content
            for script in soup.find_all('script'):
                if script.string and (match := re.search(
                        r'ajaxRequest\.open\("GET", "(.*?)",', script.string)):
                    ajax_url = f"https://www.mirrored.to{match.group(1)}"
                    break
            else:
                return None

            # Step 3: Get final download link
            data = await fetch_url(ajax_url, use_cloudscraper=True)
            soup = BeautifulSoup(data, "html.parser")

            # Fast single-pass extraction
            for link_tag in soup.find_all('a', href=True):
                full_url = f"https://www.mirrored.to{link_tag['href']}"
                try:
                    page = await fetch_url(full_url, use_cloudscraper=True)
                    if (code_wrap := BeautifulSoup(page, "html.parser").find(
                            'div', class_='code_wrap')):
                        if (code_tag := code_wrap.find('code')):
                            final_link = code_tag.get_text(strip=True)
                            if final_link.startswith("https://gofile.io/"):
                                return final_link
                except:
                    continue

            return None

        except Exception:
            return None
