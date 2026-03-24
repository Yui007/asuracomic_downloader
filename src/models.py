from pydantic import BaseModel, Field
from typing import List, Optional

class Genre(BaseModel):
    id: int
    name: str
    slug: str

class Chapter(BaseModel):
    id: int
    number: float
    title: Optional[str] = None
    slug: str
    page_count: int = 0
    series_slug: Optional[str] = None

class Manga(BaseModel):
    id: int
    slug: str
    title: str
    alt_titles: List[str] = []
    alternative_titles: Optional[str] = ""
    description: str = ""
    cover: str = ""
    banner: Optional[str] = ""
    status: str = ""
    type: str = ""
    author: str = "Unknown"
    artist: str = "Unknown"
    rating: float = 0.0
    popularity_rank: Optional[int] = 0
    bookmark_count: Optional[int] = 0
    chapter_count: Optional[int] = 0
    last_chapter_at: Optional[str] = ""
    genres: List[Genre] = []
    public_url: str = ""
    source_url: Optional[str] = ""

class Page(BaseModel):
    url: str
    width: int = 0
    height: int = 0

class ChapterImages(BaseModel):
    chapter: Chapter
    pages: List[Page]
