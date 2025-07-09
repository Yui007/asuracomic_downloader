import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from core.scraper import scrape_chapter_links, fetch_chapter_images, search_manga
from core.downloader import download_chapter, download_images_batch
from typing import List
from cli.interactive import interactive_cli
from utils import sanitizer
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.config import MAX_WORKERS
from playwright.sync_api import sync_playwright


app = typer.Typer()
console = Console()

@app.command()
def interactive():
    """
    Launch the interactive CLI mode.
    """
    interactive_cli()

@app.command()
def search(
    query: str = typer.Argument(..., help="The search query for the manga."),
    pages: int = typer.Option(1, "--pages", "-p", help="The number of pages to search."),
):
    """
    Search for a manga on AsuraComic.
    """
    console.print(f"[bold green]Searching for:[/] {query}")
    
    search_results = search_manga(query, page_limit=pages)
    
    if not search_results:
        console.print("[bold red]No manga found for your query.[/]")
        raise typer.Exit()
        
    table = Table(title="Search Results")
    table.add_column("Title", justify="left", style="cyan", no_wrap=True)
    table.add_column("Latest Chapter", justify="left", style="magenta")
    table.add_column("Link", justify="left", style="green")
    
    for result in search_results:
        table.add_row(result['title'], result['latest_chapter'], result['link'])
        
    console.print(table)

@app.command()
def get_chapters(
    url: str = typer.Argument(..., help="The URL of the manga series on AsuraComic."),
):
    """
    Scrape and list all chapter links from a given manga URL.
    """
    console.print(f"[bold green]Scraping chapters from:[/] {url}")
    
    chapter_links = scrape_chapter_links(url)
    
    if not chapter_links:
        console.print("[bold red]No chapters found. Check the URL or the site's structure.[/]")
        raise typer.Exit()
        
    table = Table(title="Available Chapters")
    table.add_column("Chapter Link", justify="left", style="cyan", no_wrap=True)
    
    for link in chapter_links:
        table.add_row(link)
        
    console.print(table)

@app.command()
def download(
    chapter_url: str = typer.Argument(..., help="The URL of the chapter to download."),
    output_dir: str = typer.Option("downloads", "--output", "-o", help="The directory to save the downloaded chapter."),
    browser=None,
):
    """
    Download a single chapter from AsuraComic.
    """
    console.print(f"[bold green]Downloading chapter from:[/] {chapter_url}")
    
    image_urls = fetch_chapter_images(chapter_url, browser=browser)
    
    if not image_urls:
        console.print(f"[bold red]No images found for chapter: {chapter_url}[/]")
        return
        
    # Extract manga and chapter name for folder creation
    try:
        manga_name = sanitizer.sanitize_filename(chapter_url.split('/series/')[1].split('/')[0])
        chapter_name = sanitizer.sanitize_filename(chapter_url.split('/chapter/')[1].replace('/', ''))
        chapter_folder = os.path.join(output_dir, manga_name, chapter_name)
    except IndexError:
        console.print("[bold red]Could not determine manga/chapter name from URL. Using default folder.[/]")
        chapter_folder = os.path.join(output_dir, "unknown_chapter")

    download_chapter(image_urls, chapter_folder)
    
    console.print(f"[bold green]Download complete![/] Chapter saved to {chapter_folder}")

@app.command()
def batch_download(
    manga_url: str = typer.Argument(..., help="The URL of the manga series on AsuraComic."),
    chapters: str = typer.Option(None, "--chapters", "-c", help="A comma-separated list of chapter numbers or a range (e.g., '1-5', '1,3,5')."),
    output_dir: str = typer.Option("downloads", "--output", "-o", help="The directory to save the downloaded chapters."),
    all_chapters: bool = typer.Option(False, "--all", help="Download all chapters."),
):
    """
    Download a batch of chapters from a manga series in parallel.
    """
    console.print(f"[bold green]Starting batch download for:[/] {manga_url}")

    all_chapter_links = scrape_chapter_links(manga_url)
    if not all_chapter_links:
        console.print("[bold red]No chapters found for this manga.[/]")
        raise typer.Exit()

    links_to_download = []
    if all_chapters:
        links_to_download = all_chapter_links
    elif chapters:
        selected_chapters = []
        if '-' in chapters:
            try:
                start, end = map(int, chapters.split('-'))
                selected_chapters = list(range(start, end + 1))
            except ValueError:
                console.print("[bold red]Invalid chapter range format. Use 'start-end'.[/]")
                raise typer.Exit()
        else:
            try:
                selected_chapters = [int(c.strip()) for c in chapters.split(',')]
            except ValueError:
                console.print("[bold red]Invalid chapter list format. Use comma-separated numbers.[/]")
                raise typer.Exit()

        for link in all_chapter_links:
            try:
                chapter_num_str = link.split('/chapter/')[1].replace('/', '')
                if '.' in chapter_num_str:
                    chapter_num = float(chapter_num_str)
                else:
                    chapter_num = int(chapter_num_str)
                
                if chapter_num in selected_chapters:
                    links_to_download.append(link)
            except (IndexError, ValueError):
                continue
    else:
        console.print("[bold red]You must specify chapters with --chapters or use --all.[/]")
        raise typer.Exit()

    if not links_to_download:
        console.print("[bold red]None of the specified chapters were found.[/]")
        raise typer.Exit()

    console.print(f"[bold yellow]Found {len(links_to_download)} chapters to download.[/]")

    images_to_download = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        console.print("[bold blue]Scraping image URLs for all chapters...[/]")
        for chapter_url in links_to_download:
            image_urls = fetch_chapter_images(chapter_url, browser=browser)
            if image_urls:
                try:
                    manga_name = sanitizer.sanitize_filename(chapter_url.split('/series/')[1].split('/')[0])
                    chapter_name = sanitizer.sanitize_filename(chapter_url.split('/chapter/')[1].replace('/', ''))
                    chapter_folder = os.path.join(output_dir, manga_name, chapter_name)
                    for i, url in enumerate(image_urls):
                        images_to_download.append((url, chapter_folder, f"page_{i+1}.jpg"))
                except IndexError:
                    console.print(f"[bold red]Could not determine manga/chapter name from URL: {chapter_url}[/]")
        browser.close()

    if not images_to_download:
        console.print("[bold red]No images found to download.[/]")
        raise typer.Exit()

    console.print(f"[bold yellow]Found {len(images_to_download)} images to download.[/]")
    download_images_batch(images_to_download)

    console.print("[bold green]Batch download complete![/]")

if __name__ == "__main__":
    app()
