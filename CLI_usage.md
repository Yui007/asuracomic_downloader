# AsuraComic Downloader - CLI Usage

This document provides instructions on how to use the command-line interface (CLI) of the AsuraComic Downloader.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/asuracomic-downloader.git
    cd asuracomic-downloader
    ```

2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Commands

### `search`

Searches for a manga on AsuraComic.

**Usage:**

```bash
python cli/main.py search [OPTIONS] QUERY
```

**Arguments:**

*   `QUERY`: The search query for the manga. (Required)

**Options:**

*   `--pages, -p`: The number of pages to search. (Default: `1`)

**Example:**

```bash
python cli/main.py search "Solo Leveling" --pages 2
```

### `get-chapters`

Scrapes and lists all available chapters for a given manga series.

**Usage:**

```bash
python cli/main.py get-chapters [OPTIONS] URL
```

**Arguments:**

*   `URL`: The URL of the manga series on AsuraComic. (Required)

**Example:**

```bash
python cli/main.py get-chapters "https://asuracomic.net/series/return-of-the-apocalypse-class-death-knight-bc6665d9"
```

### `download`

Downloads a single chapter from a given URL.

**Usage:**

```bash
python cli/main.py download [OPTIONS] CHAPTER_URL
```

**Arguments:**

*   `CHAPTER_URL`: The URL of the chapter to download. (Required)

**Options:**

*   `--output, -o`: The directory to save the downloaded chapter. (Default: `downloads`)
*   `--format, -f`: The output format (`pdf` or `cbz`). If provided, the downloaded chapter will be converted.
*   `--delete, -d`: Delete the original image folder after a successful conversion. (Only works if `--format` is used)

**Example:**

```bash
python cli/main.py download "return-of-the-apocalypse-class-death-knight-bc6665d9/chapter/1" -o my_manga --format pdf --delete
```

### `batch-download`

Downloads a batch of chapters from a manga series in parallel for faster performance. You can download by a range, a specific list, or all at once.

**Usage:**

```bash
python cli/main.py batch-download [OPTIONS] MANGA_URL
```

**Arguments:**

*   `MANGA_URL`: The URL of the manga series. (Required)

**Options:**

*   `--chapters, -c`: A comma-separated list of chapter numbers or a range (e.g., '1-5', '1,3,5').
*   `--all`: Download all chapters.
*   `--output, -o`: The directory to save the downloaded chapters. (Default: `downloads`)
*   `--format, -f`: The output format (`pdf` or `cbz`). If provided, the downloaded chapters will be converted.
*   `--delete, -d`: Delete the original image folders after a successful conversion. (Only works if `--format` is used)

**Examples:**

*   **Download a range of chapters:**
    ```bash
    python cli/main.py batch-download "https://asuracomic.net/series/return-of-the-apocalypse-class-death-knight-bc6665d9" --chapters "1-5"
    ```

*   **Download specific chapters:**
    ```bash
    python cli/main.py batch-download "https://asuracomic.net/series/return-of-the-apocalypse-class-death-knight-bc6665d9" --chapters "1,3,5"
    ```

*   **Download all chapters:**
    ```bash
    python cli/main.py batch-download "https://asuracomic.net/series/return-of-the-apocalypse-class-death-knight-bc6665d9" --all
    ```

### `interactive`

Launches an interactive CLI to browse and download manga, with support for parallel downloads.

**Usage:**

```bash
python cli/main.py interactive
```

**Features:**

*   **Search for Manga:** Search for your favorite manga and specify how many pages to look through.
*   **Browse Manga:** Enter a manga series URL to see a list of all available chapters.
*   **Select & Download:** Choose chapters to download from a list.
*   **Real-time Logs:** View download progress and logs.

**Example:**

```bash
python cli/main.py interactive
```

Upon launching, you can choose to search for a manga or enter a URL directly. The interactive wizard will guide you through the process of selecting and downloading chapters.
