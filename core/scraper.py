import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from urllib.parse import urljoin
from utils.logger import setup_logger

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
    
    # The selector is based on the provided HTML snippet
    chapter_elements = soup.select('div.pl-4.py-2.border.rounded-md a')
    
    # Use the manga_url as the base to correctly resolve relative chapter links
    chapter_links = [urljoin(manga_url, element['href']) for element in chapter_elements if element.has_attr('href')]
    
    if not chapter_links:
        logger.warning("No chapter links found. The selector might be outdated.")
    else:
        logger.info(f"Found {len(chapter_links)} chapter links.")
        
    # Reverse the list to show chapters in ascending order
    return chapter_links[::-1]

from playwright.sync_api import sync_playwright

def fetch_chapter_images(chapter_url: str) -> List[str]:
    """
    Scrapes all image links from a chapter page using Playwright.
    """
    logger.info(f"Scraping images from {chapter_url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(chapter_url, wait_until='networkidle')
            
            # Wait for the images to be loaded
            page.wait_for_selector('img.object-cover.mx-auto')
            
            image_urls = page.eval_on_selector_all('img.object-cover.mx-auto', 'elements => elements.map(el => el.src)')
            
            logger.info(f"Found {len(image_urls)} images.")
            return image_urls
        except Exception as e:
            logger.error(f"Error scraping images from {chapter_url}: {e}")
            return []
        finally:
            browser.close()

def search_manga(query: str) -> List[dict]:
    """
    Searches for a manga on AsuraComic and returns a list of dictionaries
    with title, latest_chapter, and link.
    """
    # URL-encode the query
    query = query.replace(" ", "+")
    search_url = f"https://asuracomic.net/series?page=1&name={query}"
    
    logger.info(f"Searching for manga: '{query}'")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(search_url, wait_until='networkidle')
            html_content = page.content()
        except Exception as e:
            logger.error(f"Error fetching search page with Playwright: {e}")
            return []
        finally:
            browser.close()

    if not html_content:
        logger.error("Failed to fetch search page HTML with Playwright.")
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    
    results = []
    
    # The selector is based on the provided HTML snippet
    manga_elements = soup.select('div.grid a[href*="/series/"]')

    for element in manga_elements:
        title_element = element.select_one('span.font-bold')
        if not title_element:
            continue
        
        title = title_element.text.strip()
        
        link = element['href']
        
        latest_chapter_element = title_element.find_next_sibling('span')
        latest_chapter = latest_chapter_element.text.strip() if latest_chapter_element else "No chapter found"

        results.append({
            "title": title,
            "latest_chapter": latest_chapter,
            "link": urljoin(search_url, link)
        })

    if not results:
        logger.warning(f"No manga found for '{query}'. The selectors might be outdated.")
    else:
        logger.info(f"Found {len(results)} manga for '{query}'.")
        
    return results
if __name__ == '__main__':
    # Example usage for testing
    test_url = "https://asuracomic.net/series/return-of-the-apocalypse-class-death-knight-bc6665d9"
    links = scrape_chapter_links(test_url)
    if links:
        print("Chapter Links:")
        for link in links:
            print(link)
        
        # Test fetching images from the first chapter
        if links:
            first_chapter_url = links[0]
            if not first_chapter_url.startswith('http'):
                first_chapter_url = f"https://asuracomic.net/series/{first_chapter_url}"
            images = fetch_chapter_images(first_chapter_url)
            if images:
                print("\nImages from first chapter:")
                for img in images:
                    print(img)
