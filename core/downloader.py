import os
import requests
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from typing import List
from utils.logger import setup_logger

logger = setup_logger(__name__)

def download_image(url: str, folder_path: str, filename: str):
    """
    Downloads a single image from a URL.
    """
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, filename)
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded {filename}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")

def download_chapter(image_urls: List[str], chapter_folder: str):
    """
    Downloads all images for a chapter into a specific folder.
    """
    logger.info(f"Starting download for chapter into {chapter_folder}")
    
    with Progress(
        TextColumn("[bold blue]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("[green]Downloading", total=len(image_urls))
        for i, url in enumerate(image_urls):
            filename = f"page_{i+1}.jpg"
            download_image(url, chapter_folder, filename)
            progress.update(task, advance=1)
            
    logger.info(f"Chapter download complete. Images saved in {chapter_folder}")
