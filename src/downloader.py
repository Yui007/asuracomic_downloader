import os
import re
import requests
import io
import zipfile
import img2pdf
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Callable
from PIL import Image
from .models import Manga, Chapter, Page
from .api_client import AsuraAPI

class Downloader:
    def __init__(self, settings, api: AsuraAPI):
        self.settings = settings
        self.api = api
        self.base_path = Path(settings.download_path)
        self.base_path.mkdir(exist_ok=True, parents=True)

    def sanitize_path(self, path: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', path)

    def download_image(self, url: str, path: Path) -> bool:
        for attempt in range(self.settings.retry_count):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                with open(path, "wb") as f:
                    f.write(response.content)
                return True
            except Exception:
                if attempt < self.settings.retry_count - 1:
                    import time
                    time.sleep(self.settings.retry_delay * (attempt + 1))
        return False

    def create_comic_info(self, manga: Manga, chapter: Chapter) -> str:
        # Create a simple ComicInfo.xml
        xml = f"""<?xml version="1.0" encoding="utf-8"?>
<ComicInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Series>{manga.title}</Series>
  <Number>{chapter.number}</Number>
  <Title>{chapter.title or f"Chapter {chapter.number}"}</Title>
  <Summary>{manga.description}</Summary>
  <Author>{manga.author}</Author>
  <Artist>{manga.artist}</Artist>
  <Genre>{", ".join([g.name for g in manga.genres])}</Genre>
  <Web>{manga.public_url}</Web>
</ComicInfo>"""
        return xml

    def download_chapter(self, manga: Manga, chapter: Chapter, series_slug: str, progress_callback: Optional[Callable] = None):
        manga_folder = self.base_path / self.sanitize_path(manga.title)
        chapter_folder = manga_folder / f"Chapter {chapter.number}"
        chapter_folder.mkdir(exist_ok=True, parents=True)

        pages = self.api.get_chapter_images(series_slug, chapter.slug)
        if not pages:
            return False

        image_files = []
        with ThreadPoolExecutor(max_workers=self.settings.threads_images) as executor:
            futures = {}
            for i, page in enumerate(pages):
                ext = page.url.split('.')[-1].split('?')[0] or "webp"
                img_path = chapter_folder / f"{i+1:03d}.{ext}"
                futures[executor.submit(self.download_image, page.url, img_path)] = img_path

            for future in as_completed(futures):
                img_path = futures[future]
                if future.result():
                    image_files.append(img_path)
                if progress_callback:
                    progress_callback(1)

        image_files.sort()

        # Conversion
        target_format = self.settings.download_format
        if target_format == "PDF":
            output_file = manga_folder / f"{self.sanitize_path(manga.title)} - Chapter {chapter.number}.pdf"
            with open(output_file, "wb") as f:
                f.write(img2pdf.convert([str(img) for img in image_files]))
        elif target_format == "CBZ":
            output_file = manga_folder / f"{self.sanitize_path(manga.title)} - Chapter {chapter.number}.cbz"
            with zipfile.ZipFile(output_file, 'w') as cbz:
                for img in image_files:
                    cbz.write(img, arcname=img.name)
                # Add ComicInfo.xml
                cbz.writestr("ComicInfo.xml", self.create_comic_info(manga, chapter))

        # Cleanup
        if not self.settings.keep_images and target_format != "Images":
            for img in image_files:
                img.unlink()
            if not any(chapter_folder.iterdir()):
                chapter_folder.rmdir()

        return True

    def download_manga(self, manga: Manga, chapter_range: str, overall_progress=None, chapter_progress=None):
        chapters = self.api.get_chapters(manga.slug)
        if not chapters:
            return

        selected_chapters = self.parse_range(chapter_range, chapters)
        
        overall_task = None
        if overall_progress:
            overall_task = overall_progress.add_task("[green]Total Progress", total=len(selected_chapters))

        with ThreadPoolExecutor(max_workers=self.settings.threads_chapters) as executor:
            futures = []
            for chapter in selected_chapters:
                def run_download(chap=chapter):
                    series_slug = chap.series_slug or manga.slug
                    # Handle case where series_slug might have suffix
                    if '-' in series_slug and len(series_slug.split('-')[-1]) == 8:
                         series_slug = "-".join(series_slug.split('-')[:-1])

                    pages = self.api.get_chapter_images(series_slug, chap.slug)
                    cp = chapter_progress
                    if cp is not None:
                        task_id = cp.add_task(f"[cyan]Chapter {chap.number}", total=len(pages))
                        res = self.download_chapter(manga, chap, series_slug, lambda n: cp.update(task_id, advance=n))
                        cp.remove_task(task_id)
                    else:
                        res = self.download_chapter(manga, chap, series_slug)
                    return res

                futures.append(executor.submit(run_download))

            for future in as_completed(futures):
                if overall_progress is not None and overall_task is not None:
                    overall_progress.update(overall_task, advance=1)

    def parse_range(self, range_str: str, all_chapters: List[Chapter]) -> List[Chapter]:
        if range_str.lower() == "all":
            return all_chapters
        
        selected_numbers = set()
        parts = range_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = map(float, part.split('-'))
                for chap in all_chapters:
                    if start <= chap.number <= end:
                        selected_numbers.add(chap.number)
            else:
                try:
                    num = float(part)
                    selected_numbers.add(num)
                except ValueError:
                    pass
        
        return [c for c in all_chapters if c.number in selected_numbers]
