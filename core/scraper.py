import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urljoin
from utils.logger import setup_logger
from playwright.sync_api import sync_playwright
import asyncio
from playwright.async_api import async_playwright as async_playwright_api

# Setting up logger
logger = setup_logger(__name__)

def fetch_html(url: str) -> Optional[str]:
    """
    Fetches HTML content from a URL.
    """
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def scrape_chapter_links(manga_url: str) -> List[str]:
    """
    Scrapes all chapter links from a manga series page.
    """
    logger.info(f"Scraping chapter links from {manga_url}")
    html_content = fetch_html(manga_url)
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    
    chapter_elements = soup.select('div.pl-4.py-2.border.rounded-md a')
    
    chapter_links = [urljoin(manga_url, element['href']) for element in chapter_elements if element.has_attr('href')]
    
    if not chapter_links:
        logger.warning("No chapter links found. The selector might be outdated.")
    else:
        logger.info(f"Found {len(chapter_links)} chapter links.")
        
    return chapter_links[::-1]

def fetch_chapter_images(chapter_url: str, browser=None) -> List[str]:
    """
    Scrapes all image links from a chapter page using Playwright.
    If a browser instance is provided, it uses it; otherwise, it creates a new one.
    """
    logger.info(f"Scraping images from {chapter_url}")

    def scrape_action(p_browser):
        page = p_browser.new_page()
        try:
            page.goto(chapter_url, wait_until='networkidle', timeout=60000)  # Increased timeout
            page.wait_for_selector('img.object-cover.mx-auto', timeout=10000)
            image_urls = page.eval_on_selector_all('img.object-cover.mx-auto', 'elements => elements.map(el => el.src)')
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

async def search_manga_async(query: str, page_limit: int = 1) -> List[dict]:
    """
    Asynchronously searches for a manga on AsuraComic with pagination and returns a list of dictionaries.
    """
    base_url = "https://asuracomic.net/"
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
                    logger.info(f"No more results found on page {page_num}.")
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
                logger.error(f"An error occurred on page {page_num}: {e}")
                break
        
        await browser.close()

    if not all_results:
        logger.warning(f"No manga found for '{query}'. The selectors might be outdated.")
    else:
        logger.info(f"Found {len(all_results)} manga for '{query}'.")
        
    return all_results

def search_manga(query: str, page_limit: int = 1) -> List[dict]:
    """
    Synchronous wrapper for search_manga_async.
    """
    return asyncio.run(search_manga_async(query, page_limit))

if __name__ == '__main__':
    # Example usage for testing
    test_query = "Solo"
    results = search_manga(test_query, page_limit=2)
    if results:
        print(f"Found {len(results)} results for '{test_query}':")
        for res in results:
            print(f"  - {res['title']} ({res['latest_chapter']})")
