import os
import requests
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from typing import List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import setup_logger
from core.config import MAX_WORKERS
from utils.converter import convert_to_pdf, convert_to_cbz

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

def download_chapter(image_urls: List[str], chapter_folder: str, progress_callback: Callable = None):
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
            for i, future in enumerate(as_completed(futures)):
                try:
                    future.result()  # Raise any exceptions
                    if progress_callback:
                        progress_callback(i + 1, len(image_urls))
                except Exception as e:
                    logger.error(f"An error occurred during download: {e}")
                progress.update(task, advance=1)

    logger.info(f"Chapter download complete. Images saved in {chapter_folder}")

def download_images_batch(images_data: List[tuple], format_choice: str, delete_original: bool, progress_callback: Callable = None, status_callback: Callable = None):
    """
    Downloads a batch of images from a list of tuples containing (url, folder_path, filename).
    """
    logger.info(f"Starting batch download of {len(images_data)} images.")
    total_images = len(images_data)

    with Progress(
        TextColumn("[bold blue]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("[green]Downloading Images", total=total_images)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(download_image, url, folder_path, filename)
                for url, folder_path, filename in images_data
            ]
            for i, future in enumerate(as_completed(futures)):
                try:
                    future.result()
                    if progress_callback:
                        progress_callback(i + 1, total_images)
                except Exception as e:
                    logger.error(f"An error occurred during batch image download: {e}")
                progress.update(task, advance=1)

    logger.info("Batch image download complete.")
    if status_callback:
        status_callback("Batch download complete!")

    if format_choice != "None":
        if status_callback:
            status_callback(f"Converting chapters to {format_choice}...")
        downloaded_chapter_folders = sorted(list(set(item[1] for item in images_data)))

        for chapter_folder in downloaded_chapter_folders:
            try:
                chapter_name = os.path.basename(chapter_folder)
                image_files = [os.path.join(chapter_folder, f) for f in sorted(os.listdir(chapter_folder)) if f.endswith(('.jpg', '.png', '.jpeg'))]
                if not image_files:
                    continue

                output_path = os.path.join(os.path.dirname(chapter_folder), f"{chapter_name}.{format_choice}")
                if format_choice.lower() == 'pdf':
                    convert_to_pdf(image_files, output_path)
                elif format_choice.lower() == 'cbz':
                    convert_to_cbz(image_files, output_path)
                
                if status_callback:
                    status_callback(f"Converted {chapter_name} to {format_choice}.")

                if delete_original:
                    if status_callback:
                        status_callback(f"Deleting original images for {chapter_name}...")
                    for f in image_files:
                        os.remove(f)
                    os.rmdir(chapter_folder)
                    if status_callback:
                        status_callback(f"Original images for {chapter_name} deleted.")
            except Exception as e:
                logger.error(f"Error converting {chapter_folder}: {e}")
                if status_callback:
                    status_callback(f"Error converting {chapter_folder}: {str(e)}")
