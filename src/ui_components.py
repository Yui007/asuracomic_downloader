import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.prompt import Prompt, IntPrompt, Confirm
from typing import List, Any, Optional
from .models import Manga, Chapter

console = Console()

class UI:
    @staticmethod
    def display_welcome():
        console.print(Panel.fit(
            "[bold cyan]AsuraComic Downloader[/bold cyan]\n[italic white]A modern, fast CLI for AsuraScans[/italic white]",
            border_style="cyan"
        ))

    @staticmethod
    def display_search_results(mangas: List[Manga]):
        table = Table(title="Search Results", show_header=True, header_style="bold magenta")
        table.add_column("No.", style="dim", width=4)
        table.add_column("Title")
        table.add_column("Status", justify="center")
        table.add_column("Chapters", justify="right")
        table.add_column("Rating", justify="right")

        for i, m in enumerate(mangas):
            table.add_row(
                str(i + 1),
                f"[bold white]{m.title}[/bold white]",
                f"[green]{m.status}[/green]" if m.status.lower() == "ongoing" else f"[yellow]{m.status}[/yellow]",
                "N/A", # Need to fetch chapter count separately or use search count if available
                f"[yellow]{m.rating:.2f}[/yellow]"
            )
        console.print(table)

    @staticmethod
    def display_settings(settings):
        table = Table(title="Current Settings", show_header=True, header_style="bold blue")
        table.add_column("Key")
        table.add_column("Value")
        
        table.add_row("Download Format", f"[cyan]{settings.download_format}[/cyan]")
        table.add_row("Keep Images", "[green]Yes[/green]" if settings.keep_images else "[red]No[/red]")
        table.add_row("Chapter Threads", str(settings.threads_chapters))
        table.add_row("Image Threads", str(settings.threads_images))
        table.add_row("Retry Count", str(settings.retry_count))
        table.add_row("Retry Delay", f"{settings.retry_delay}s")
        table.add_row("Logging", "[green]Enabled[/green]" if settings.enable_logging else "[red]Disabled[/red]")
        table.add_row("Download Path", settings.download_path)
        limit_str = "All" if settings.chapter_list_limit <= 0 else str(settings.chapter_list_limit)
        table.add_row("Chapter List Limit", f"[cyan]{limit_str}[/cyan]")

        console.print(table)

    @staticmethod
    def display_manga_info(manga: Manga):
        console.print(f"\n[bold green]Manga:[/bold green] {manga.title}")
        if manga.alternative_titles:
            console.print(f"[bold dim]Alt Titles:[/bold dim] {manga.alternative_titles}")
        
        console.print(f"[bold cyan]Genres:[/bold cyan] {', '.join([g.name for g in manga.genres])}")
        console.print(f"[bold blue]Status:[/bold blue] {manga.status} | [bold blue]Type:[/bold blue] {manga.type}")
        console.print(f"[bold yellow]Rating:[/bold yellow] {manga.rating:.2f} | [bold yellow]Rank:[/bold yellow] #{manga.popularity_rank}")
        console.print(f"[bold magenta]Author:[/bold magenta] {manga.author} | [bold magenta]Artist:[/bold magenta] {manga.artist}")
        
        if manga.description:
            # Clean HTML tags from description if any
            desc = re.sub('<[^<]+?>', '', manga.description)
            console.print(Panel(desc.strip(), title="Description", border_style="dim"))

    @staticmethod
    def display_chapter_list(chapters: List[Chapter], limit: int = 20):
        if not chapters:
            return

        # Handle limit (0 = all)
        if limit <= 0 or limit >= len(chapters):
            display_chaps = chapters
        else:
            display_chaps = chapters[-limit:]

        table = Table(
            title=f"[bold cyan]Chapter List[/bold cyan] [dim]({len(chapters)} total)[/dim]",
            show_header=True,
            header_style="bold magenta",
            box=None,
            padding=(0, 2),
            title_justify="left",
            border_style="dim"
        )
        
        table.add_column("Index", style="dim cyan", justify="right")
        table.add_column("Chapter Number", style="bold white")
        table.add_column("Title", style="italic gray50")
        
        if limit > 0 and len(chapters) > limit:
            console.print(f"\n[dim italic]Showing last {limit} chapters...[/dim italic]")

        for i, c in enumerate(display_chaps):
            # Calculate original index
            idx = len(chapters) - len(display_chaps) + i + 1
            
            chapter_str = f"Chapter [bold]{c.number}[/bold]"
            title_str = c.title if c.title else ""
            
            table.add_row(
                str(idx),
                chapter_str,
                title_str
            )
        
        console.print(Panel(table, border_style="cyan", padding=(1, 1)))

    @staticmethod
    def get_progress_bars():
        overall_progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        )
        chapter_progress = Progress(
            TextColumn("  "),
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[dim]{task.description}"),
            BarColumn(bar_width=20),
            TaskProgressColumn(),
            console=console
        )
        return overall_progress, chapter_progress
