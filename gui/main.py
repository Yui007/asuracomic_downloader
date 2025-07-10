import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox, QComboBox, QHBoxLayout, QFileDialog, QGroupBox, QMessageBox
from PyQt5.QtGui import QPalette, QBrush, QPixmap, QIntValidator
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.scraper import search_manga, scrape_chapter_links

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

        # Get Chapters Functionality
        get_chapters_group_box = QGroupBox("Get Chapters")
        get_chapters_layout = QVBoxLayout()

        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Manga Series URL:"))
        self.manga_url_input = QLineEdit()
        url_layout.addWidget(self.manga_url_input)
        get_chapters_layout.addLayout(url_layout)

        self.get_chapters_button = QPushButton("Get Chapters")
        self.get_chapters_button.clicked.connect(self.perform_get_chapters)
        get_chapters_layout.addWidget(self.get_chapters_button)

        self.chapters_display = QTextEdit()
        self.chapters_display.setReadOnly(True)
        get_chapters_layout.addWidget(self.chapters_display)

        get_chapters_group_box.setLayout(get_chapters_layout)
        self.layout.addWidget(get_chapters_group_box)

    def perform_get_chapters(self):
        manga_url = self.manga_url_input.text()
        if not manga_url:
            self.chapters_display.setText("Please enter a manga series URL.")
            return

        self.chapters_display.setText(f"Fetching chapters from: {manga_url}...")
        
        # Create a worker thread for the get chapters operation
        self.get_chapters_thread = GetChaptersWorker(manga_url)
        self.get_chapters_thread.chapters_finished.connect(self.display_chapters)
        self.get_chapters_thread.chapters_error.connect(self.handle_get_chapters_error)
        self.get_chapters_button.setEnabled(False) # Disable button during operation
        self.get_chapters_thread.start()

    def display_chapters(self, chapter_links):
        self.get_chapters_button.setEnabled(True) # Re-enable button
        if chapter_links:
            formatted_chapters = "\n".join(chapter_links)
            self.chapters_display.setText(formatted_chapters)
        else:
            self.chapters_display.setText("No chapters found for this URL. Check the URL or the site's structure.")

    def handle_get_chapters_error(self, error_message):
        self.get_chapters_button.setEnabled(True) # Re-enable button
        QMessageBox.critical(self, "Get Chapters Error", error_message)
        self.chapters_display.setText(f"Error fetching chapters: {error_message}")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AsuraComicDownloaderGUI()
    window.show()
    sys.exit(app.exec_())