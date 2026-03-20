import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from utils.logger import setup_logger
from playwright.sync_api import sync_playwright
import asyncio
from playwright.async_api import async_playwright as async_playwright_api

# Logger
logger = setup_logger(__name__)

# ==============================
# ✅ HELPER FUNCTION (IMPORTANT)
# ==============================
def extract_manga_and_chapter(url: str):
    """
    Extract manga name and chapter number from AsuraScans URL.
    """
    try:
        parts = urlparse(url).path.strip("/").split("/")
        # ['comics', 'manga-name', 'chapter', '1']

        manga_name = parts[1]
        chapter_number = parts[-1]

        return manga_name, chapter_number
    except Exception:
        return "unknown_manga", "unknown_chapter"


# ==============================
# FETCH HTML (fallback, not used much now)
# ==============================
def fetch_html(url: str) -> Optional[str]:
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


# ==============================
# ✅ SCRAPE CHAPTER LINKS (FIXED)
# ==============================
def scrape_chapter_links(manga_url: str) -> List[str]:
    logger.info(f"Scraping chapter links from {manga_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(manga_url, wait_until='networkidle', timeout=60000)

            # FIX: use attached instead of visible
            page.wait_for_selector("a[href*='/chapter/']", state="attached", timeout=15000)

            elements = page.query_selector_all("a[href*='/chapter/']")

            chapter_links = []
            for el in elements:
                href = el.get_attribute("href")
                if href:
                    full_url = urljoin(manga_url, href)
                    chapter_links.append(full_url)

            if not chapter_links:
                logger.warning("No chapter links found.")
            else:
                logger.info(f"Found {len(chapter_links)} chapter links.")

            return list(set(chapter_links))[::-1]

        except Exception as e:
            logger.error(f"Error scraping chapters: {e}")
            return []

        finally:
            browser.close()


# ==============================
# ✅ SCRAPE CHAPTER IMAGES (FIXED)
# ==============================
def fetch_chapter_images(chapter_url: str, browser=None) -> List[str]:
    logger.info(f"Scraping images from {chapter_url}")

    def scrape_action(p_browser):
        page = p_browser.new_page()
        try:
            page.goto(chapter_url, wait_until='networkidle', timeout=60000)

            # FIX: generic selector + attached
            page.wait_for_selector("img", state="attached", timeout=15000)

            # Scroll to load lazy images (IMPORTANT)
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            image_urls = page.eval_on_selector_all(
                "img",
                """elements => elements
                    .map(el => el.src || el.getAttribute('data-src'))
                    .filter(src => src && src.startsWith('http') && !src.includes('logo'))
                """
            )

            logger.info(f"Found {len(image_urls)} images in {chapter_url}")
            return image_urls

        except Exception as e:
            logger.error(f"Error scraping images from {chapter_url}: {e}")
            return []

        finally:
            page.close()

    if browser:
        return scrape_action(browser)
    else:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                return scrape_action(browser)
            finally:
                browser.close()


# ==============================
# SEARCH (UNCHANGED)
# ==============================
async def search_manga_async(query: str, page_limit: int = 1) -> List[dict]:
    base_url = "https://asuracomic.com/"
    query_encoded = query.replace(" ", "+")
    all_results = []

    async with async_playwright_api() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for page_num in range(1, page_limit + 1):
            search_url = f"{base_url}series?page={page_num}&name={query_encoded}"
            logger.info(f"Searching for manga: '{query}' on page {page_num}")

            try:
                await page.goto(search_url, wait_until='networkidle', timeout=60000)
                await page.wait_for_selector("a[href^='series/']", timeout=10000)

                blocks = await page.query_selector_all("a[href^='series/']")
                if not blocks:
                    break

                for block in blocks:
                    href = await block.get_attribute("href")
                    title_el = await block.query_selector("span.block.font-bold")
                    chapter_el = await block.query_selector("span.text-\\[13px\\].text-\\[\\#999\\]")

                    if not (title_el and chapter_el):
                        continue

                    title = await title_el.inner_text()
                    latest_chapter = await chapter_el.inner_text()

                    all_results.append({
                        "title": title.strip(),
                        "latest_chapter": latest_chapter.strip(),
                        "link": urljoin(base_url, href)
                    })

            except Exception as e:
                logger.error(f"Error on page {page_num}: {e}")
                break

        await browser.close()

    if not all_results:
        logger.warning(f"No manga found for '{query}'.")
    else:
        logger.info(f"Found {len(all_results)} manga.")

    return all_results


def search_manga(query: str, page_limit: int = 1) -> List[dict]:
    return asyncio.run(search_manga_async(query, page_limit))