from .base import AnimeCard, EpisodeCard, post_url, fetch_url
from Tools.logger import get_logger
import json
from urllib.parse import quote
from playwright.async_api import async_playwright
import asyncio


log = get_logger(__name__)

MSG_FORMAT = "**{name}**\n\n**Alt Titles:** `{alt_titles}`\n**Censored:** `{is_censored}`\n**Genres:** `{tags}`\n\n`{description}`"


class HanimeTVWebs:
    __slots__ = ('name', 'base_url', 'search_header', 'sf')

    def __init__(self):
        self.name = "HanimeTV"
        self.sf = "HT"
        self.base_url = "https://hanime.tv"
        self.search_header = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }

    async def search(self, query: str):
        results = []
        try:
            search_url = "https://cached.freeanimehentai.net/api/v10/search_hvs"
            data = json.dumps({
                "search_text": query,
                "tags": [],
                "tags_mode": "AND",
                "brands": [],
                "blacklist": [],
                "order_by": "created_at_unix",
                "ordering": "desc",
                "page": 0
            })
            
            
            response = await post_url(
                search_url, data=data, use_cloudscraper=True,
                headers=self.search_header
            )

            if not response or 'hits' not in response:
                return

            rdata = json.loads(response['hits'])

            for data in rdata:
                #poster = "https://api.shanksytprem.workers.dev/proxy?url=" + quote(data['poster_url'], safe="")
                results.append(AnimeCard(
                    url=f"https://hanime.tv/videos/hentai/{data['slug']}",
                    title=data['name'],
                    poster="",
                    data={"slug": data['slug']},
                    web_data=self.sf,
                    msg=MSG_FORMAT.format(
                        name=data['name'],
                        alt_titles=', '.join(data.get('titles', [])[:3]),
                        is_censored=data.get('is_censored', 'Unknown'),
                        tags=', '.join(data.get('tags',[])[:5]),
                        description=data.get('description','')[:300]
                    )))
            
            return results

        except Exception as e:
            log.debug(f"{self.name} search error: {e}")

    async def get_info(self, animeclass: AnimeCard) -> AnimeCard:
        return animeclass 

    async def get_episodes(self, animeclass: AnimeCard, page: int = 1):
        try:
            yield EpisodeCard(
                url=animeclass.url,
                title=animeclass.title,
                data=animeclass.data,
                anime_title="")
        except Exception as e:
            log.debug(f"{self.name} get episodes error: {e}")

    async def get_downloading_links(self, episodeclass: EpisodeCard):
        episodeclass.download_links = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            try:
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                
                page = await context.new_page()
                tokens = {"sig": None, "ver": None, "tme": None}
                token_event = asyncio.Event()
                
                async def handle_request(req):
                    h = req.headers
                    sig = h.get("x-signature")
                    ver = h.get("x-signature-version")
                    tme = h.get("x-time")

                    if sig and ver and tme and not token_event.is_set():
                        tokens["sig"] = sig
                        tokens["ver"] = ver
                        tokens["tme"] = tme
                        token_event.set()
                    
                context.on("request", handle_request)
                await page.goto(episodeclass.url, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                
                nuxt_data = await page.evaluate("() => window.__NUXT__")
                hv = nuxt_data["state"]["data"]["video"]["hentai_video"]
                video_id = hv["id"]
                
                episodeclass.title = hv["name"]
                episodeclass.anime_title = hv["name"]
                
                await page.wait_for_timeout(3000)
                await asyncio.wait_for(token_event.wait(), timeout=20)
                
                manifest_api = f"https://cached.freeanimehentai.net/api/v8/guest/videos/{video_id}/manifest"
                headers = {
                    "x-signature": tokens["sig"],
                    "x-signature-version": tokens["ver"],
                    "x-time": tokens["tme"],
                    "referer": "https://hanime.tv/",
                    "origin": "https://hanime.tv",
                    "user-agent": await page.evaluate("() => navigator.userAgent")
                }
                
                api_resp = await context.request.get(
                    manifest_api,
                    headers=headers
                )
                
                if api_resp.status == 200:
                    data = await api_resp.json()
                    server = data['videos_manifest']['servers'][0]
                    for stream in server.get('streams', []):
                        if stream.get('url'):
                            episodeclass.download_links.append({
                                "quality": f"{stream.get('height', 'Unknown')}p",
                                "link": stream['url'],
                            })
            except Exception as e:
                log.debug(f"{self.name} download links error: {e}")
            finally:
                try: 
                    await browser.close()
                except Exception: 
                    pass
