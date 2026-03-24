import time
import requests
from typing import List, Optional
from .models import Manga, Chapter, Genre, Page
import logging

class AsuraAPI:
    BASE_URL = "https://api.asurascans.com/api"

    def __init__(self, retry_count=3, retry_delay=2, enable_logging=False):
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.logger = logging.getLogger("AsuraAPI")
        if not enable_logging:
            self.logger.addHandler(logging.NullHandler())
            self.logger.propagate = False

    def _request(self, method: str, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        url = f"{self.BASE_URL}/{endpoint}"
        for attempt in range(self.retry_count):
            try:
                response = requests.request(method, url, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        return None

    def search(self, query: str) -> List[Manga]:
        data = self._request("GET", "series", params={"search": query})
        if not data or "data" not in data:
            return []
        
        mangas = []
        for item in data["data"]:
            mangas.append(Manga(
                id=item["id"],
                slug=item["slug"],
                title=item["title"],
                alt_titles=item.get("alt_titles", []),
                alternative_titles=item.get("alternative_titles", ""),
                description=item.get("description", ""),
                cover=item.get("cover", ""),
                banner=item.get("banner", ""),
                status=item.get("status", ""),
                type=item.get("type", ""),
                author=item.get("author", "Unknown"),
                artist=item.get("artist", "Unknown"),
                rating=item.get("rating", 0.0),
                popularity_rank=item.get("popularity_rank", 0),
                bookmark_count=item.get("bookmark_count", 0),
                chapter_count=item.get("chapter_count", 0),
                last_chapter_at=item.get("last_chapter_at", ""),
                genres=[Genre(**g) for g in item.get("genres", [])],
                public_url=item.get("public_url", ""),
                source_url=item.get("source_url", "")
            ))
        return mangas

    def get_series_info(self, series_slug: str) -> Optional[Manga]:
        # series_slug should be the one with the suffix if applicable
        data = self._request("GET", f"series/{series_slug}")
        if not data or "series" not in data:
            return None
        
        item = data["series"]
        return Manga(
            id=item["id"],
            slug=item["slug"],
            title=item["title"],
            alt_titles=item.get("alt_titles", []),
            alternative_titles=item.get("alternative_titles", ""),
            description=item.get("description", ""),
            cover=item.get("cover", ""),
            banner=item.get("banner", ""),
            status=item.get("status", ""),
            type=item.get("type", ""),
            author=item.get("author", "Unknown"),
            artist=item.get("artist", "Unknown"),
            rating=item.get("rating", 0.0),
            popularity_rank=item.get("popularity_rank", 0),
            bookmark_count=item.get("bookmark_count", 0),
            chapter_count=item.get("chapter_count", 0),
            last_chapter_at=item.get("last_chapter_at", ""),
            genres=[Genre(**g) for g in item.get("genres", [])],
            public_url=item.get("public_url", ""),
            source_url=item.get("source_url", "")
        )

    def get_chapters(self, series_slug: str) -> List[Chapter]:
        data = self._request("GET", f"series/{series_slug}/chapters")
        if not data or "data" not in data:
            return []
        
        chapters = []
        for item in data["data"]:
            chapters.append(Chapter(
                id=item["id"],
                number=float(item["number"]),
                title=item.get("title"),
                slug=item["slug"],
                page_count=item.get("page_count", 0),
                series_slug=item.get("series_slug")
            ))
        return sorted(chapters, key=lambda x: x.number)

    def get_chapter_images(self, series_base_slug: str, chapter_uuid: str) -> List[Page]:
        # Note: series_base_slug is needed here, e.g. "swordmasters-youngest-son"
        data = self._request("GET", f"series/{series_base_slug}/chapters/{chapter_uuid}")
        if not data or "data" not in data or "chapter" not in data["data"]:
            return []
        
        pages = []
        for page in data["data"]["chapter"].get("pages", []):
            pages.append(Page(
                url=page["url"],
                width=page.get("width", 0),
                height=page.get("height", 0)
            ))
        return pages
