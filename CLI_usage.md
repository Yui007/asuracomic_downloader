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

**Example:**

```bash
python cli/main.py download "return-of-the-apocalypse-class-death-knight-bc6665d9/chapter/1" -o my_manga
```

### `batch-download`

Downloads a batch of chapters from a manga series, either by a range, a specific list, or all at once.

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

Launches an interactive TUI (Textual User Interface) to browse and download manga.

**Usage:**

```bash
python cli/main.py interactive
```

**Features:**

*   **Browse Manga:** Enter a manga series URL to see a list of all available chapters.
*   **Select & Download:** Use the arrow keys to navigate the chapter list and press `Enter` to download a selected chapter.
*   **Real-time Logs:** View download progress and logs in a separate panel.
*   **Dark Mode:** Toggle dark mode by pressing `d`.
*   **Quit:** Exit the application by pressing `q`.

**Example:**

```bash
python cli/main.py interactive
```

Upon launching, you will be prompted to enter a manga series URL. After entering the URL, the TUI will fetch and display the chapters for you to browse and download.
