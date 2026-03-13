from asyncio import to_thread
from aiohttp import ClientSession, ClientTimeout
from cloudscraper import create_scraper
from playwright.async_api import async_playwright
from typing import Optional, Dict, Any, List

_SCRAPER = create_scraper()


class AnimeCard:
    __slots__ = ('url', 'title', 'poster', 'msg', 'data', 'web_data')

    def __init__(self, url: str, title: str, poster: str = "", msg: str = "", 
                 data: Optional[Dict] = None, web_data: str = ""):
        self.url = url
        self.title = title
        self.poster = poster
        self.msg = msg
        self.data = data or {}
        self.web_data = web_data

    def unique(self) -> str:
        return str(hash(f"{self.url}/{self.web_data}"))

    def __repr__(self) -> str:
        return f"AnimeCard(title='{self.title}', url='{self.url}')"


class EpisodeCard:
    __slots__ = ('url', 'title', 'data', 'anime_title', 'download_links')

    def __init__(self, url: str, title: str, anime_title: str, 
                 download_links: Optional[List] = None, data: Optional[Dict] = None):
        self.url = url
        self.title = title
        self.data = data or {}
        self.anime_title = anime_title
        self.download_links = download_links or []

    def __str__(self) -> str:
        return f"EpisodeCard( {self.title} | {self.anime_title} | {self.url} )"

    def unique(self) -> str:
        return str(hash(f"{self.url}/{self.title}"))


async def fetch_url(url: str, **kwargs) -> Any:
    """Fetch URL content with multiple backend options."""
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        **kwargs.pop('headers', {})
    }

    timeout = kwargs.pop('timeout', 30)
    use_cloudscraper = kwargs.pop('use_cloudscraper', False)
    return_json = kwargs.pop('return_json', False)
    raise_for_status = kwargs.pop('raise_for_status', True)
    use_playwright = kwargs.pop('use_playwright', False)

    try:
        if use_playwright:
            return await _fetch_with_playwright(url, headers, **kwargs)
        elif use_cloudscraper:
            return await _fetch_with_cloudscraper(url, headers, timeout, return_json, raise_for_status, **kwargs)
        else:
            return await _fetch_with_aiohttp(url, headers, timeout, return_json, raise_for_status, **kwargs)
    except Exception as e:
        raise Exception(f"Failed to fetch {url}: {str(e)}") from e


async def _fetch_with_playwright(url: str, headers: Dict, **kwargs) -> str:
    """Fetch using Playwright for JavaScript-rendered content."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            extra_http_headers=headers
        )
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")
        content = await page.content()
        await browser.close()
        return content


async def _fetch_with_cloudscraper(url: str, headers: Dict, timeout: int, 
                                   return_json: bool, raise_for_status: bool, **kwargs) -> Any:
    """Fetch using cloudscraper (synchronous, run in thread)."""
    response = await to_thread(
        _SCRAPER.get, url,
        headers=headers, 
        timeout=timeout, 
        **kwargs
    )
    if raise_for_status and response.status_code >= 400:
        raise Exception(f"Request failed with status {response.status_code}")
    return response.json() if return_json else response.text


async def _fetch_with_aiohttp(url: str, headers: Dict, timeout: int, 
                              return_json: bool, raise_for_status: bool, **kwargs) -> Any:
    """Fetch using aiohttp (asynchronous)."""
    timeout_settings = ClientTimeout(total=timeout)
    async with ClientSession(headers=headers, timeout=timeout_settings) as session:
        async with session.get(url, **kwargs) as response:
            if raise_for_status:
                response.raise_for_status()
            return await response.json() if return_json else await response.text()


async def post_url(url: str, **kwargs) -> Any:
    """POST data to URL."""
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }

    # Merge custom headers
    custom_headers = kwargs.pop('headers', {})
    headers.update(custom_headers)

    use_cloudscraper = kwargs.pop('use_cloudscraper', False)
    return_json = kwargs.pop('return_json', False)
    timeout = kwargs.pop('timeout', 60)

    try:
        if use_cloudscraper:
            response = await to_thread(
                _SCRAPER.post, url,
                headers=headers, timeout=timeout, **kwargs
            )
            return response.json() if return_json else response.text
        else:
            timeout_settings = ClientTimeout(total=timeout)
            async with ClientSession(headers=headers, timeout=timeout_settings) as session:
                async with session.post(url, **kwargs) as response:
                    return await response.json() if return_json else await response.text()
    except Exception as e:
        raise Exception(f"Failed to POST to {url}: {str(e)}") from e
