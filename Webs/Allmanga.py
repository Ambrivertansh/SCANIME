
from .base import AnimeCard, EpisodeCard, fetch_url  # Use same base import
from Tools.logger import get_logger
import json

log = get_logger(__name__)

API_URL = "https://api.allanime.day/api"
VIDEO_BASE_URL = "https://wp.youtube-anime.com/aln.youtube-anime.com"

MSG_FORMAT = "**{name} | {eng_name}**\n\n**ID:** `{id}`\n**Genres:** `{genres}`\n**Episodes:** `{episodes}`\n**Status:** `{status}`\n**Season:** `{season}`\n**Year:** `{year}`\n\n**Url:** {url}"

class AllAnimeWebs:
    __slots__ = ('name', 'headers', 'sf')

    def __init__(self):
        self.name = "AllAnime"
        self.sf = "AA"
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Origin": "https://allanime.to",
            "Referer": "https://allanime.to/"
        }

    async def search(self, query: str):
        variables = {
            "search": {"query": query},
            "limit": 26,
            "page": 1,
            "translationType": "sub",
            "countryOrigin": "ALL"
        }
        extensions = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "06327bc10dd682e1ee7e07b6db9c16e9ad2fd56c1b769e47513128cd5c9fc77a"
            }
        }
        params = {
            "variables": json.dumps(variables),
            "extensions": json.dumps(extensions)
        }
        try:
            data = await fetch_url(API_URL, headers=self.headers, params=params, return_json=True)
            shows = data.get('data', {}).get('shows', {}).get('edges', [])
            results = []
            for anime in shows:
                eng_name = anime.get('englishName') or anime.get('nativeName') or anime.get('name')
                genres = anime.get('genres', []) if 'genres' in anime else "Unknown"
                poster = anime.get('sampleAnime', {}).get("thumbnail", None) or anime.get('thumbnail', None)
                results.append(
                    AnimeCard(
                        url=f"https://allmanga.to/bangumi/{anime['_id']}",
                        title=anime['name'],
                        poster=poster,
                        data=anime,
                        web_data=self.sf,
                        msg=MSG_FORMAT.format(
                            name=anime['name'],
                            eng_name=eng_name,
                            id=anime['_id'],
                            genres=genres,
                            episodes=anime.get('episodeCount', "N/A"),
                            status=anime.get('status', "N/A"),
                            season=anime.get('season', {}).get('quarter', "N/A"),
                            year=anime.get('season', {}).get('year', "N/A"),
                            url=f"https://allmanga.to/bangumi/{anime['_id']}"
                        )
                    )
                )
            return results
        except Exception as e:
            log.debug(f"[AllAnime] search error: {e}")
            return []

    async def get_info(self, animeclass: AnimeCard):
        variables = {"_id": animeclass.data["_id"]}
        extensions = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "9d7439c90f203e534ca778c4901f9aa2d3ad42c06243ab2c5e6b79612af32028"
            }
        }
        params = {
            "variables": json.dumps(variables),
            "extensions": json.dumps(extensions)
        }
        try:
            data = await fetch_url(API_URL, headers=self.headers, params=params, return_json=True)
            show = data.get('data', {}).get('show', {})
            animeclass.data = show
            animeclass.title = show.get('name')
            animeclass.poster = show.get('thumbnail')
            return animeclass
        except Exception as e:
            log.debug(f"[AllAnime] get_info error: {e}")
            return animeclass

    async def get_episodes(self, animeclass: AnimeCard, page: int = 1):
        total_eps = int(animeclass.data.get('episodeCount', 0))
        if not total_eps:
            return
        variables = {
            "showId": animeclass.data['_id'],
            "episodeNumStart": 1,
            "episodeNumEnd": total_eps
        }
        extensions = {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "c8f3ac51f598e630a1d09d7f7fb6924cff23277f354a23e473b962a367880f7d"
            }
        }
        params = {
            "variables": json.dumps(variables),
            "extensions": json.dumps(extensions)
        }
        try:
            data = await fetch_url(API_URL, headers=self.headers, params=params, return_json=True)
            episodes = data.get('data', {}).get('episodeInfos', [])

            for ep in episodes:
                ep_num = ep.get('episodeIdNum')
                ep_title = ep.get('notes', f"Episode {ep_num}")
                vid_sub_path = (ep.get('vidInforssub') or {}).get('vidPath')
                vid_dub_path = (ep.get('vidInforsdub') or {}).get('vidPath')
                yield EpisodeCard(
                    url="",
                    title=f"Episode {ep_num}",
                    data={
                        "sub_url": VIDEO_BASE_URL + vid_sub_path if vid_sub_path else None,
                        "dub_url": VIDEO_BASE_URL + vid_dub_path if vid_dub_path else None,
                        "ep_num": ep_num,
                        "ep_title": ep_title,
                    },
                    anime_title=animeclass.title,
                )
        except Exception as e:
            log.debug(f"[AllAnime] get_episodes error: {e}")

    async def get_downloading_links(self, episodeclass: EpisodeCard):
        episodeclass.download_links = []
        try:
            if episodeclass.url:
                episodeclass.download_links.append({
                    "quality": "1080p",
                    "link": episodeclass.url
                })
        except Exception as e:
            log.debug(f"[AllAnime] get_downloading_links error: {e}")
