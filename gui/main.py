import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox, QComboBox, QHBoxLayout, QFileDialog, QGroupBox, QMessageBox, QListWidget, QListWidgetItem
from PyQt5.QtGui import QPalette, QBrush, QPixmap, QIntValidator
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.scraper import search_manga, scrape_chapter_links, fetch_chapter_images
from core.downloader import download_chapter, download_images_batch
from utils.converter import convert_to_pdf, convert_to_cbz
from utils.sanitizer import sanitize_filename
from playwright.sync_api import sync_playwright

class AsuraComicDownloaderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AsuraComic Downloader")
        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.init_ui()
        self.apply_styles()

    def apply_styles(self):
        # Set background image
        background_image_path = "assets/background.png"
        try:
            palette = self.palette()
            pixmap = QPixmap(background_image_path)
            if pixmap.isNull():
                print(f"Warning: Could not load background image from {background_image_path}")
            else:
                palette.setBrush(QPalette.Window, QBrush(pixmap))
                self.setPalette(palette)
                self.setAutoFillBackground(True)
        except Exception as e:
            print(f"Error setting background image: {e}")

        # Apply transparent glass button, QLineEdit, and QTextEdit styles
        style_sheet = """
            QPushButton {
                background-color: rgba(255, 255, 255, 50); /* White with 50% transparency */
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 5px;
                padding: 8px 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 80);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 120);
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 50);
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 50);
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
            QLabel {
                color: white; /* Ensure labels are visible against the background */
            }
            QGroupBox {
                color: white; /* Ensure group box titles are visible */
            }
            QListWidget {
                background-color: rgba(255, 255, 255, 50);
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
        """
        self.setStyleSheet(style_sheet)

    def init_ui(self):
        # Search Functionality
        search_group_box = QGroupBox("Search Manga")
        search_layout = QVBoxLayout()

        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("Manga Query:"))
        self.search_query_input = QLineEdit()
        query_layout.addWidget(self.search_query_input)
        search_layout.addLayout(query_layout)

        pages_layout = QHBoxLayout()
        pages_layout.addWidget(QLabel("Number of Pages:"))
        self.search_pages_input = QLineEdit("1")
        self.search_pages_input.setValidator(QIntValidator())
        pages_layout.addWidget(self.search_pages_input)
        search_layout.addLayout(pages_layout)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)

        self.search_results_display = QTextEdit()
        self.search_results_display.setReadOnly(True)
        search_layout.addWidget(self.search_results_display)

        search_group_box.setLayout(search_layout)
        self.layout.addWidget(search_group_box)

        # Download Chapters Functionality
        download_group_box = QGroupBox("Download Chapters")
        download_layout = QVBoxLayout()

        manga_url_layout = QHBoxLayout()
        manga_url_layout.addWidget(QLabel("Manga Series URL:"))
        self.manga_url_input = QLineEdit()
        manga_url_layout.addWidget(self.manga_url_input)
        download_layout.addLayout(manga_url_layout)

        self.get_chapters_button = QPushButton("Get Chapters")
        self.get_chapters_button.clicked.connect(self.perform_get_chapters)
        download_layout.addWidget(self.get_chapters_button)

        self.chapters_list_widget = QListWidget()
        download_layout.addWidget(self.chapters_list_widget)

        selection_buttons_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_chapters)
        selection_buttons_layout.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self.deselect_all_chapters)
        selection_buttons_layout.addWidget(self.deselect_all_button)
        download_layout.addLayout(selection_buttons_layout)

        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(QLabel("Output Directory:"))
        self.download_output_dir_input = QLineEdit("downloads")
        output_dir_layout.addWidget(self.download_output_dir_input)
        self.browse_output_dir_button = QPushButton("Browse")
        self.browse_output_dir_button.clicked.connect(self.browse_download_output_dir)
        output_dir_layout.addWidget(self.browse_output_dir_button)
        download_layout.addLayout(output_dir_layout)

        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Convert Format:"))
        self.download_format_combo = QComboBox()
        self.download_format_combo.addItem("None")
        self.download_format_combo.addItem("pdf")
        self.download_format_combo.addItem("cbz")
        format_layout.addWidget(self.download_format_combo)
        download_layout.addLayout(format_layout)

        self.delete_original_checkbox = QCheckBox("Delete original images after conversion")
        download_layout.addWidget(self.delete_original_checkbox)

        self.download_button = QPushButton("Download Selected Chapters")
        self.download_button.clicked.connect(self.perform_batch_download)
        download_layout.addWidget(self.download_button)

        self.download_status_display = QTextEdit()
        self.download_status_display.setReadOnly(True)
        download_layout.addWidget(self.download_status_display)

        download_group_box.setLayout(download_layout)
        self.layout.addWidget(download_group_box)

    def select_all_chapters(self):
        for i in range(self.chapters_list_widget.count()):
            item = self.chapters_list_widget.item(i)
            item.setCheckState(Qt.Checked)

    def deselect_all_chapters(self):
        for i in range(self.chapters_list_widget.count()):
            item = self.chapters_list_widget.item(i)
            item.setCheckState(Qt.Unchecked)

    def browse_download_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.download_output_dir_input.setText(directory)

    def perform_batch_download(self):
        manga_url = self.manga_url_input.text()
        output_dir = self.download_output_dir_input.text()
        format_choice = self.download_format_combo.currentText()
        delete_original = self.delete_original_checkbox.isChecked()

        selected_indices = []
        for i in range(self.chapters_list_widget.count()):
            item = self.chapters_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected_indices.append(i + 1)

        if not manga_url:
            QMessageBox.warning(self, "Warning", "Please enter a manga series URL.")
            return
        if not selected_indices:
            QMessageBox.warning(self, "Warning", "Please select chapters to download.")
            return

        chapters_selection = ",".join(map(str, selected_indices))

        self.download_status_display.setText(f"Starting batch download for: {manga_url}...")
        
        self.batch_download_thread = BatchDownloadWorker(manga_url, chapters_selection, False, output_dir, format_choice, delete_original)
        self.batch_download_thread.batch_download_finished.connect(self.display_batch_download_status)
        self.batch_download_thread.batch_download_error.connect(self.handle_batch_download_error)
        self.download_button.setEnabled(False)
        self.batch_download_thread.start()

    def display_batch_download_status(self, message):
        self.download_button.setEnabled(True)
        self.download_status_display.append(message)

    def handle_batch_download_error(self, error_message):
        self.download_button.setEnabled(True)
        QMessageBox.critical(self, "Batch Download Error", error_message)
        self.download_status_display.append(f"Error during batch download: {error_message}")

    def perform_get_chapters(self):
        manga_url = self.manga_url_input.text()
        if not manga_url:
            QMessageBox.warning(self, "Warning", "Please enter a manga series URL.")
            return

        self.download_status_display.setText(f"Fetching chapters from: {manga_url}...")
        
        self.get_chapters_thread = GetChaptersWorker(manga_url)
        self.get_chapters_thread.chapters_finished.connect(self.display_chapters)
        self.get_chapters_thread.chapters_error.connect(self.handle_get_chapters_error)
        self.get_chapters_button.setEnabled(False)
        self.get_chapters_thread.start()

    def display_chapters(self, chapter_links):
        self.get_chapters_button.setEnabled(True)
        self.chapters_list_widget.clear()
        if chapter_links:
            self.chapter_links = chapter_links
            for i, link in enumerate(chapter_links):
                item_text = f"Chapter {i+1}: {link.split('/')[-2]}"
                item = QListWidgetItem(item_text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.chapters_list_widget.addItem(item)
            self.download_status_display.append("Chapters loaded. Select chapters to download.")
        else:
            self.download_status_display.append("No chapters found for this URL.")

    def handle_get_chapters_error(self, error_message):
        self.get_chapters_button.setEnabled(True)
        QMessageBox.critical(self, "Get Chapters Error", error_message)
        self.download_status_display.append(f"Error fetching chapters: {error_message}")

    def perform_search(self):
        query = self.search_query_input.text()
        pages = self.search_pages_input.text()
        if not query:
            self.search_results_display.setText("Please enter a manga query.")
            return

        self.search_results_display.setText(f"Searching for '{query}' across {pages} pages...")
        
        # Create a worker thread for the search operation
        self.search_thread = SearchWorker(query, int(pages))
        self.search_thread.search_finished.connect(self.display_search_results)
        self.search_thread.search_error.connect(self.handle_search_error)
        self.search_button.setEnabled(False) # Disable button during search
        self.search_thread.start()

    def display_search_results(self, results):
        self.search_button.setEnabled(True) # Re-enable button
        if results:
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(f"{i}. Title: {result['title']}\n   Latest Chapter: {result['latest_chapter']}\n   Link: {result['link']}\n")
            self.search_results_display.setText("\n".join(formatted_results))
        else:
            self.search_results_display.setText("No manga found for your query.")

    def handle_search_error(self, error_message):
        self.search_button.setEnabled(True) # Re-enable button
        QMessageBox.critical(self, "Search Error", error_message)
        self.search_results_display.setText(f"Error during search: {error_message}")

class SearchWorker(QThread):
    search_finished = pyqtSignal(list)
    search_error = pyqtSignal(str)

    def __init__(self, query, page_limit):
        super().__init__()
        self.query = query
        self.page_limit = page_limit

    def run(self):
        try:
            results = search_manga(self.query, page_limit=self.page_limit)
            self.search_finished.emit(results)
        except Exception as e:
            self.search_error.emit(str(e))

class GetChaptersWorker(QThread):
    chapters_finished = pyqtSignal(list)
    chapters_error = pyqtSignal(str)

    def __init__(self, manga_url):
        super().__init__()
        self.manga_url = manga_url

    def run(self):
        try:
            chapter_links = scrape_chapter_links(self.manga_url)
            self.chapters_finished.emit(chapter_links)
        except Exception as e:
            self.chapters_error.emit(str(e))

class BatchDownloadWorker(QThread):
    batch_download_finished = pyqtSignal(str)
    batch_download_error = pyqtSignal(str)

    def __init__(self, manga_url, chapters_selection, all_chapters, output_dir, format_choice, delete_original):
        super().__init__()
        self.manga_url = manga_url
        self.chapters_selection = chapters_selection
        self.all_chapters = all_chapters
        self.output_dir = output_dir
        self.format_choice = format_choice
        self.delete_original = delete_original

    def run(self):
        try:
            self.batch_download_finished.emit("Fetching chapter links...")
            chapter_links = scrape_chapter_links(self.manga_url)
            if not chapter_links:
                self.batch_download_error.emit("No chapter links found.")
                return

            selected_chapters_urls = []
            if self.all_chapters:
                selected_chapters_urls = chapter_links
            else:
                selection_parts = self.chapters_selection.replace(' ', '').split(',')
                for part in selection_parts:
                    if '-' in part:
                        try:
                            start, end = map(int, part.split('-'))
                            for i in range(start - 1, end):
                                if 0 <= i < len(chapter_links):
                                    selected_chapters_urls.append(chapter_links[i])
                        except ValueError:
                            self.batch_download_error.emit(f"Invalid range in selection: {part}")
                            return
                    else:
                        try:
                            chapter_num = int(part)
                            if 0 < chapter_num <= len(chapter_links):
                                selected_chapters_urls.append(chapter_links[chapter_num - 1])
                        except ValueError:
                            self.batch_download_error.emit(f"Invalid chapter number in selection: {part}")
                            return
            
            selected_chapters_urls = sorted(list(set(selected_chapters_urls)), key=chapter_links.index)

            if not selected_chapters_urls:
                self.batch_download_error.emit("No valid chapters selected for download.")
                return

            manga_name = sanitize_filename(self.manga_url.split('/series/')[1].split('/')[0])
            manga_output_dir = os.path.join(self.output_dir, manga_name)
            os.makedirs(manga_output_dir, exist_ok=True)

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                for chapter_url in selected_chapters_urls:
                    try:
                        chapter_name = sanitize_filename(chapter_url.split('/chapter/')[1].replace('/', ''))
                        chapter_folder = os.path.join(manga_output_dir, chapter_name)
                        
                        self.batch_download_finished.emit(f"Downloading {chapter_name}...")
                        
                        image_urls = fetch_chapter_images(chapter_url, browser=browser)
                        if not image_urls:
                            self.batch_download_finished.emit(f"No images found for {chapter_name}. Skipping.")
                            continue

                        download_chapter(image_urls, chapter_folder)
                        self.batch_download_finished.emit(f"Finished downloading {chapter_name}.")

                        if self.format_choice != "None":
                            self.batch_download_finished.emit(f"Converting {chapter_name} to {self.format_choice}...")
                            image_files = [os.path.join(chapter_folder, f) for f in sorted(os.listdir(chapter_folder)) if f.endswith(('.jpg', '.png', '.jpeg'))]
                            if image_files:
                                output_path = os.path.join(manga_output_dir, f"{chapter_name}.{self.format_choice}")
                                if self.format_choice.lower() == 'pdf':
                                    convert_to_pdf(image_files, output_path)
                                elif self.format_choice.lower() == 'cbz':
                                    convert_to_cbz(image_files, output_path)
                                self.batch_download_finished.emit(f"Conversion complete for {chapter_name}.")

                                if self.delete_original:
                                    self.batch_download_finished.emit(f"Deleting original images for {chapter_name}...")
                                    for f in image_files:
                                        os.remove(f)
                                    os.rmdir(chapter_folder)
                                    self.batch_download_finished.emit(f"Original images for {chapter_name} deleted.")
                    except Exception as e:
                        self.batch_download_error.emit(f"Error processing chapter {chapter_url}: {str(e)}")
                browser.close()
            self.batch_download_finished.emit("Batch download complete.")
        except Exception as e:
            self.batch_download_error.emit(str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AsuraComicDownloaderGUI()
    window.show()
    sys.exit(app.exec_())
