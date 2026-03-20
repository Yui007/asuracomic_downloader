import typer
from rich.console import Console
from rich.prompt import Prompt
import os
from core import scraper, downloader
from utils import logger, sanitizer
from utils.converter import convert_to_cbz, convert_to_pdf, get_image_files, delete_images
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

console = Console()


def interactive_cli():
    console.print("[bold cyan]AsuraComic Downloader - Interactive Mode[/bold cyan]")
    console.print("Welcome! This wizard will guide you through downloading your favorite manga.")

    choice = Prompt.ask(
        "Do you want to search for a manga or enter a URL directly?",
        choices=["search", "url"],
        default="search"
    )

    if choice == "search":
        query = Prompt.ask("Enter the manga name to search for")
        page_limit_str = Prompt.ask("How many pages to search?", default="1")

        try:
            page_limit = int(page_limit_str)
        except ValueError:
            console.print("[bold red]Invalid number. Defaulting to 1.[/bold red]")
            page_limit = 1

        with console.status(f"[bold green]Searching for '{query}'..."):
            search_results = scraper.search_manga(query, page_limit=page_limit)

        if not search_results:
            console.print("[bold red]No manga found.[/bold red]")
            return

        from rich.table import Table
        table = Table(title="Search Results")
        table.add_column("Num", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Latest Chapter", style="yellow")
        table.add_column("Link", style="green")

        for i, result in enumerate(search_results, 1):
            table.add_row(str(i), result['title'], result['latest_chapter'], result['link'])

        console.print(table)

        selection = Prompt.ask("Enter the number", default="1")

        try:
            manga_url = search_results[int(selection) - 1]['link']
        except:
            console.print("[bold red]Invalid selection.[/bold red]")
            return

    else:
        manga_url = Prompt.ask("Enter the manga series URL")

    # Fetch chapters
    with console.status("[bold green]Fetching chapters..."):
        chapter_links = scraper.scrape_chapter_links(manga_url)

    if not chapter_links:
        console.print("[bold red]No chapters found.[/bold red]")
        return

    console.print(f"[bold green]Found {len(chapter_links)} chapters![/bold green]")

    # Chapter selection
    selection = Prompt.ask("Select chapters (all / 1-5 / 1,3,5)")
    download_path = Prompt.ask("Download path", default="./downloads")

    selected_chapters = []

    if selection.lower() == 'all':
        selected_chapters = chapter_links
    else:
        try:
            parts = selection.split(',')
            for part in parts:
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    for i in range(start, end + 1):
                        selected_chapters.append(chapter_links[i - 1])
                else:
                    selected_chapters.append(chapter_links[int(part) - 1])
        except:
            console.print("[bold red]Invalid selection.[/bold red]")
            return

    # ==============================
    # ✅ DOWNLOAD PREPARATION (FIXED)
    # ==============================
    images_to_download = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        console.print("[bold blue]Scraping images...[/]")

        for chapter_url in selected_chapters:
            image_urls = scraper.fetch_chapter_images(chapter_url, browser=browser)

            if not image_urls:
                continue

            try:
                parts = urlparse(chapter_url).path.strip("/").split("/")

                # ['comics', 'manga-name', 'chapter', '1']
                manga_name = sanitizer.sanitize_filename(parts[1])
                chapter_name = sanitizer.sanitize_filename(f"chapter_{parts[-1]}")

            except Exception:
                console.print(f"[yellow]Fallback naming for: {chapter_url}[/]")
                manga_name = "asura_manga"
                chapter_name = f"chapter_{len(images_to_download)}"

            chapter_folder = os.path.join(download_path, manga_name, chapter_name)

            for i, url in enumerate(image_urls):
                images_to_download.append((url, chapter_folder, f"page_{i+1}.jpg"))

        browser.close()

    if not images_to_download:
        console.print("[bold red]No images found to download.[/bold red]")
        return

    console.print(f"[bold yellow]Found {len(images_to_download)} images[/]")

    # Conversion
    convert_choice = Prompt.ask(
        "Convert to?",
        choices=["none", "pdf", "cbz"],
        default="none"
    )

    delete_original = False
    if convert_choice != "none":
        delete_original = Prompt.ask(
            "Delete original images?",
            choices=["yes", "no"],
            default="no"
        ) == "yes"

    downloader.download_images_batch(
        images_to_download,
        convert_choice,
        delete_original,
        status_callback=console.print
    )

    console.print("[bold green]Download complete![/bold green]")


if __name__ == "__main__":
    typer.run(interactive_cli)