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

    # Ask user if they want to search or use a URL
    choice = Prompt.ask("Do you want to search for a manga or enter a URL directly?", choices=["search", "url"], default="search")

    if choice == "search":
        query = Prompt.ask("Enter the manga name to search for")
        page_limit_str = Prompt.ask("How many pages to search?", default="1")
        try:
            page_limit = int(page_limit_str)
        except ValueError:
            console.print("[bold red]Invalid number of pages. Defaulting to 1.[/bold red]")
            page_limit = 1

        with console.status(f"[bold green]Searching for '{query}'..."):
            search_results = scraper.search_manga(query, page_limit=page_limit)

        if not search_results:
            console.print("[bold red]No manga found for your query.[/bold red]")
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

        selection = Prompt.ask("Enter the number of the manga you want to download", default="1")
        try:
            manga_url = search_results[int(selection) - 1]['link']
        except (ValueError, IndexError):
            console.print("[bold red]Invalid selection.[/bold red]")
            return
    else:
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
