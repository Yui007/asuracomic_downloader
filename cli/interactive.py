# cli/interactive.py

"""
Interactive CLI for AsuraComic Downloader.
"""

import typer
from rich.console import Console
from rich.prompt import Prompt

from core import scraper, downloader
from utils import logger, sanitizer

# Initialize Rich Console
console = Console()


def interactive_cli():
    """
    Launch the interactive CLI mode.
    """
    console.print("[bold cyan]AsuraComic Downloader - Interactive Mode[/bold cyan]")
    console.print("Welcome! This wizard will guide you through downloading your favorite manga.")

    # Get manga URL from user
    manga_url = Prompt.ask("Enter the manga series URL")

    # Fetch chapter links
    with console.status("[bold green]Fetching chapter list..."):
        chapter_links = scraper.scrape_chapter_links(manga_url)

    if not chapter_links:
        console.print("[bold red]Could not find any chapters. Please check the URL.[/bold red]")
        return

    console.print(f"[bold green]Found {len(chapter_links)} chapters![/bold green]")

    # Display chapters in a table
    from rich.table import Table

    table = Table(title="Available Chapters")
    table.add_column("Num", style="cyan")
    table.add_column("Chapter URL", style="magenta")

    for i, link in enumerate(chapter_links, 1):
        table.add_row(str(i), link)

    console.print(table)

    # Prompt for chapter selection
    selection = Prompt.ask(
        "Which chapters do you want to download? (e.g., 'all', '1-5', '1,3,5')"
    )

    # Prompt for download path
    download_path = Prompt.ask("Enter the download path", default="./downloads")

    # Parse chapter selection
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
        except (ValueError, IndexError):
            console.print("[bold red]Invalid chapter selection.[/bold red]")
            return

    # Start download process
    for chapter_url in selected_chapters:
        console.print(f"\n[bold cyan]Downloading chapter: {chapter_url}[/bold cyan]")
        
        # Fetch image URLs
        with console.status("[bold green]Fetching image links..."):
            image_urls = scraper.fetch_chapter_images(chapter_url)

        if not image_urls:
            console.print("[bold red]Could not find any images for this chapter.[/bold red]")
            continue

        # Create chapter folder
        manga_title = sanitizer.sanitize_filename(manga_url.split('/')[-1])
        chapter_name = sanitizer.sanitize_filename(chapter_url.split('/')[-1])
        chapter_folder = f"{download_path}/{manga_title}/{chapter_name}"

        # Download chapter
        downloader.download_chapter(image_urls, chapter_folder)

    console.print("\n[bold green]All selected chapters have been downloaded![/bold green]")


if __name__ == "__main__":
    typer.run(interactive_cli)