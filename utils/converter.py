# utils/converter.py

import os
import zipfile
from PIL import Image
from natsort import natsorted

def get_image_files(directory: str) -> list[str]:
    """
    Gets a natsorted list of image files from a directory.

    Args:
        directory: The directory to search for images.

    Returns:
        A list of full paths to the image files.
    """
    image_files = []
    for file in os.listdir(directory):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            image_files.append(os.path.join(directory, file))
    return natsorted(image_files)

def convert_to_pdf(image_files: list[str], output_path: str):
    """
    Converts a list of images to a PDF file.

    Args:
        image_files: A list of full paths to the image files.
        output_path: The path to save the PDF file.
    """
    if not image_files:
        return

    images = [Image.open(f).convert('RGB') for f in image_files]
    if images:
        images[0].save(output_path, save_all=True, append_images=images[1:])

def convert_to_cbz(image_files: list[str], output_path: str):
    """
    Converts a list of images to a CBZ file.

    Args:
        image_files: A list of full paths to the image files.
        output_path: The path to save the CBZ file.
    """
    with zipfile.ZipFile(output_path, 'w') as cbz:
        for i, image_file in enumerate(image_files):
            cbz.write(image_file, f"{i+1:03d}{os.path.splitext(image_file)[1]}")

def delete_images(image_files: list[str]):
    """
    Deletes a list of image files.

    Args:
        image_files: A list of full paths to the image files to delete.
    """
    for image_file in image_files:
        try:
            os.remove(image_file)
        except OSError as e:
            print(f"Error deleting file {image_file}: {e}")
