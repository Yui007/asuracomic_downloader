import os
import requests
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import setup_logger
from core.config import MAX_WORKERS

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
    Downloads all images for a chapter into a specific folder using threading.
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
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(download_image, url, chapter_folder, f"page_{i+1}.jpg")
                for i, url in enumerate(image_urls)
            ]
            for future in as_completed(futures):
                try:
                    future.result()  # Raise any exceptions
                except Exception as e:
                    logger.error(f"An error occurred during download: {e}")
                progress.update(task, advance=1)

    logger.info(f"Chapter download complete. Images saved in {chapter_folder}")

def download_images_batch(images_data: List[tuple]):
    """
    Downloads a batch of images from a list of tuples containing (url, folder_path, filename).
    """
    logger.info(f"Starting batch download of {len(images_data)} images.")

    with Progress(
        TextColumn("[bold blue]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("[green]Downloading Images", total=len(images_data))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(download_image, url, folder_path, filename)
                for url, folder_path, filename in images_data
            ]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"An error occurred during batch image download: {e}")
                progress.update(task, advance=1)

    logger.info("Batch image download complete.")
