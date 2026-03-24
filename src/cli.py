import typer
import sys
import re
from typing import Optional
from rich.live import Live
from rich.console import Group
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

from .config_manager import ConfigManager
from .api_client import AsuraAPI
from .downloader import Downloader
from .ui_components import UI, console
from .models import Manga, Chapter

app = typer.Typer(help="AsuraComic Downloader CLI")

config_mgr = ConfigManager()
api = AsuraAPI(
    retry_count=config_mgr.settings.retry_count,
    retry_delay=config_mgr.settings.retry_delay,
    enable_logging=config_mgr.settings.enable_logging
)
downloader = Downloader(config_mgr.settings, api)

def search_menu():
    query = Prompt.ask("[bold yellow]Enter Search Query[/bold yellow]")
    mangas = api.search(query)
    if not mangas:
        console.print("[red]No manga found.[/red]")
        return

    UI.display_search_results(mangas)
    choice = IntPrompt.ask("[bold yellow]Select Manga No. (0 to cancel)[/bold yellow]", default=0)
    if choice <= 0 or choice > len(mangas):
        return

    manga = mangas[choice - 1]
    download_interactive(manga)

def download_interactive(manga: Manga):
    UI.display_manga_info(manga)
    
    chapters = api.get_chapters(manga.slug)
    if not chapters:
        console.print("[red]Could not retrieve chapters.[/red]")
        return

    UI.display_chapter_list(chapters, limit=config_mgr.settings.chapter_list_limit)
    console.print(f"[bold yellow]Total Chapters:[/bold yellow] {len(chapters)}")
    console.print(f"[bold magenta]Range Example:[/bold magenta] 1-10, 15, 20-25 or 'all'")
    range_str = Prompt.ask("[bold yellow]Enter Chapter Range[/bold yellow]", default="all")

    overall_progress, chapter_progress = UI.get_progress_bars()
    
    with Live(Group(overall_progress, chapter_progress), console=console, refresh_per_second=10):
        downloader.download_manga(manga, range_str, overall_progress, chapter_progress)

    console.print("[bold green]Download Complete![/bold green]")

def settings_menu():
    while True:
        UI.display_settings(config_mgr.settings)
        console.print("\n[bold magenta]1.[/bold magenta] Change Download Format")
        console.print("[bold magenta]2.[/bold magenta] Toggle Keep Images")
        console.print("[bold magenta]3.[/bold magenta] Change Chapter Threads")
        console.print("[bold magenta]4.[/bold magenta] Change Image Threads")
        console.print("[bold magenta]5.[/bold magenta] Toggle Logging")
        console.print("[bold magenta]6.[/bold magenta] Change Download Path")
        console.print("[bold magenta]7.[/bold magenta] Change Chapter List Limit (0 = All)")
        console.print("[bold magenta]0.[/bold magenta] Back to Main Menu")
        
        choice = IntPrompt.ask("\n[bold yellow]Select Option[/bold yellow]", default=0)
        
        if choice == 0:
            break
        elif choice == 1:
            fmt = Prompt.ask("Enter Format (PDF, CBZ, Images)", choices=["PDF", "CBZ", "Images"], default=config_mgr.settings.download_format)
            config_mgr.update_setting("download_format", fmt)
        elif choice == 2:
            keep = Confirm.ask("Keep individual images after conversion?", default=config_mgr.settings.keep_images)
            config_mgr.update_setting("keep_images", keep)
        elif choice == 3:
            threads = IntPrompt.ask("Enter Concurrent Chapter Downloads", default=config_mgr.settings.threads_chapters)
            config_mgr.update_setting("threads_chapters", threads)
        elif choice == 4:
            threads = IntPrompt.ask("Enter Concurrent Image Downloads", default=config_mgr.settings.threads_images)
            config_mgr.update_setting("threads_images", threads)
        elif choice == 5:
            log = Confirm.ask("Enable Logging?", default=config_mgr.settings.enable_logging)
            config_mgr.update_setting("enable_logging", log)
        elif choice == 6:
            path = Prompt.ask("Enter Download Path", default=config_mgr.settings.download_path)
            config_mgr.update_setting("download_path", path)
        elif choice == 7:
            limit = IntPrompt.ask("Enter Chapter List Limit (0 for all)", default=config_mgr.settings.chapter_list_limit)
            config_mgr.update_setting("chapter_list_limit", limit)

@app.command()
def interactive():
    """Start the interactive CLI menu."""
    while True:
        UI.display_welcome()
        console.print("[bold magenta]1.[/bold magenta] Download Manga by URL")
        console.print("[bold magenta]2.[/bold magenta] Search for a manga by title")
        console.print("[bold magenta]3.[/bold magenta] Settings")
        console.print("[bold magenta]4.[/bold magenta] Exit")
        
        choice = IntPrompt.ask("\n[bold yellow]Select Option[/bold yellow]", default=4)
        
        if choice == 4:
            console.print("[yellow]Exiting...[/yellow]")
            sys.exit(0)
        elif choice == 1:
            url = Prompt.ask("[bold yellow]Enter Manga URL[/bold yellow]")
            # Extract slug from URL: https://asurascans.com/comics/swordmasters-youngest-son-f6174291
            match = re.search(r'/comics/([^/]+)', url)
            if match:
                slug = match.group(1)
                manga = api.get_series_info(slug)
                if manga:
                    download_interactive(manga)
                else:
                    console.print("[red]Manga not found.[/red]")
            else:
                console.print("[red]Invalid URL format.[/red]")
        elif choice == 2:
            search_menu()
        elif choice == 3:
            settings_menu()

if __name__ == "__main__":
    app()
