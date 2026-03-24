import sys
import os
import re
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QLineEdit, 
                             QGridLayout, QScrollArea, QFrame, QProgressBar, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QAbstractItemView, QFileDialog, QSpinBox, QCheckBox, 
                             QComboBox)
from PyQt6.QtCore import Qt, QSize, QThreadPool, QRunnable, pyqtSignal, QObject, QEvent
from PyQt6.QtGui import QIcon, QFont, QColor, QPixmap
import qtawesome as qta
import requests

from ..config_manager import ConfigManager
from ..api_client import AsuraAPI
from ..downloader import Downloader
from ..models import Manga, Chapter
from .widgets import MangaCard, GlassCard

class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int) # task_id, value

class TaskWorker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))

class GUIProgressBridge(QObject):
    task_added = pyqtSignal(int, str, int) # task_id, name, total
    task_updated = pyqtSignal(int, int) # task_id, advance
    task_removed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.tasks = {}
        self.next_id = 0

    def add_task(self, description, total=100):
        task_id = self.next_id
        self.next_id += 1
        self.tasks[task_id] = description
        self.task_added.emit(task_id, description, total)
        return task_id

    def update(self, task_id, advance=0):
        self.task_updated.emit(task_id, advance)

    def remove_task(self, task_id):
        self.task_removed.emit(task_id)

class MainWindow(QMainWindow):
    def __init__(self, config_mgr):
        super().__init__()
        self.config_mgr = config_mgr
        self.api = AsuraAPI(
            retry_count=config_mgr.settings.retry_count,
            retry_delay=config_mgr.settings.retry_delay,
            enable_logging=config_mgr.settings.enable_logging
        )
        self.downloader = Downloader(config_mgr.settings, self.api)
        self.threadpool = QThreadPool()
        
        self.progress_bridge = GUIProgressBridge()
        self.progress_bridge.task_added.connect(self.on_task_added)
        self.progress_bridge.task_updated.connect(self.on_task_updated)
        self.progress_bridge.task_removed.connect(self.on_task_removed)
        self.task_id_to_row = {}
        
        self.setWindowTitle("AsuraComic Downloader")
        self.setMinimumSize(1100, 750)
        
        self.init_ui()
        self.load_stylesheet()
        
    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 30, 10, 10)
        
        self.logo = QLabel("ASURA")
        self.logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d2ff; margin-bottom: 30px;")
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sidebar_layout.addWidget(self.logo)
        
        self.nav_buttons = []
        tabs = [
            ("Home", 0, "fa5s.home"), 
            ("Search", 1, "fa5s.search"), 
            ("Manga Info", 2, "fa5s.info-circle"), 
            ("Progress", 3, "fa5s.tasks"), 
            ("Settings", 4, "fa5s.cog")
        ]
        for text, index, icon_name in tabs:
            btn = QPushButton(text)
            btn.setIcon(qta.icon(icon_name, color="#8888aa"))
            btn.setIconSize(QSize(20, 20))
            btn.setObjectName("nav_button")
            btn.setCheckable(True)
            if index == 0: btn.setChecked(True)
            btn.clicked.connect(lambda checked, idx=index: self.switch_tab(idx))
            self.sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
        self.sidebar_layout.addStretch()
        self.main_layout.addWidget(self.sidebar)
        
        # Content Stack
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)
        
        # Init Tabs
        self.init_home_tab()
        self.init_search_tab()
        self.init_mangainfo_tab()
        self.init_progress_tab()
        self.init_settings_tab()

    def load_stylesheet(self):
        style_path = os.path.join(os.path.dirname(__file__), "style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def init_home_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome = QLabel("Welcome to AsuraComic Downloader")
        welcome.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(welcome)
        
        subtitle = QLabel("Start by searching for your favorite manga or paste a URL")
        subtitle.setStyleSheet("color: #8888aa; font-size: 16px;")
        layout.addWidget(subtitle)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste Manga URL here...")
        self.url_input.setFixedWidth(500)
        layout.addWidget(self.url_input)
        
        dl_btn = QPushButton("Go to Manga")
        dl_btn.setObjectName("primary_button")
        dl_btn.setFixedWidth(200)
        dl_btn.clicked.connect(self.handle_url_input)
        layout.addWidget(dl_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.stack.addWidget(tab)

    def init_search_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        search_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for manga...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_btn = QPushButton("Search")
        search_btn.setObjectName("primary_button")
        search_btn.clicked.connect(self.perform_search)
        
        search_bar.addWidget(self.search_input)
        search_bar.addWidget(search_btn)
        layout.addLayout(search_bar)
        
        # Results Grid
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setStyleSheet("background: transparent; border: none;")
        self.results_widget = QWidget()
        self.results_grid = QGridLayout(self.results_widget)
        self.results_scroll.setWidget(self.results_widget)
        layout.addWidget(self.results_scroll)
        
        self.stack.addWidget(tab)

    def init_mangainfo_tab(self):
        tab = QWidget()
        # This will be populated dynamically when a manga is selected
        self.manga_layout = QVBoxLayout(tab)
        self.stack.addWidget(tab)

    def init_progress_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel("Download Progress"))
        
        self.progress_table = QTableWidget(0, 3)
        self.progress_table.setHorizontalHeaderLabels(["Chapter", "Status", "Progress"])
        header = self.progress_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.progress_table)
        
        self.stack.addWidget(tab)

    def init_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(50, 50, 50, 50)
        
        card = GlassCard()
        card_layout = QGridLayout(card)
        self.settings_layout = card_layout # Save for later
        layout.addWidget(card)
        layout.addStretch()

        settings = self.config_mgr.settings
        
        # Row 0: Download Format
        card_layout.addWidget(QLabel("Download Format:"), 0, 0)
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["PDF", "CBZ", "Images"])
        self.fmt_combo.setCurrentText(settings.download_format)
        self.fmt_combo.currentTextChanged.connect(lambda v: self.config_mgr.update_setting("download_format", v))
        card_layout.addWidget(self.fmt_combo, 0, 1)

        # Row 1: Keep Images
        card_layout.addWidget(QLabel("Keep Images after conversion:"), 1, 0)
        self.keep_cb = QCheckBox()
        self.keep_cb.setChecked(settings.keep_images)
        self.keep_cb.toggled.connect(lambda v: self.config_mgr.update_setting("keep_images", v))
        card_layout.addWidget(self.keep_cb, 1, 1)

        # Row 2: Threads Chapters
        card_layout.addWidget(QLabel("Chapter Threads:"), 2, 0)
        self.chap_threads = QSpinBox()
        self.chap_threads.setRange(1, 10)
        self.chap_threads.setValue(settings.threads_chapters)
        self.chap_threads.valueChanged.connect(lambda v: self.config_mgr.update_setting("threads_chapters", v))
        card_layout.addWidget(self.chap_threads, 2, 1)

        # Row 3: Threads Images
        card_layout.addWidget(QLabel("Image Threads:"), 3, 0)
        self.img_threads = QSpinBox()
        self.img_threads.setRange(1, 20)
        self.img_threads.setValue(settings.threads_images)
        self.img_threads.valueChanged.connect(lambda v: self.config_mgr.update_setting("threads_images", v))
        card_layout.addWidget(self.img_threads, 3, 1)

        # Row 4: Chapter List Limit
        card_layout.addWidget(QLabel("Chapter List Limit (0=All):"), 4, 0)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 1000)
        self.limit_spin.setValue(settings.chapter_list_limit)
        self.limit_spin.valueChanged.connect(lambda v: self.config_mgr.update_setting("chapter_list_limit", v))
        card_layout.addWidget(self.limit_spin, 4, 1)
        
        self.stack.addWidget(tab)

    def perform_search(self):
        query = self.search_input.text()
        if not query: return
        
        # Clear grid
        for i in reversed(range(self.results_grid.count())): 
            item = self.results_grid.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
            
        worker = TaskWorker(self.api.search, query)
        worker.signals.finished.connect(self.display_search_results)
        self.threadpool.start(worker)

    def display_search_results(self, mangas):
        for i, manga in enumerate(mangas):
            card = MangaCard(manga)
            card.clicked.connect(self.show_manga_info)
            self.results_grid.addWidget(card, i // 4, i % 4)

    def handle_url_input(self):
        url = self.url_input.text()
        match = re.search(r'/comics/([^/]+)', url)
        if match:
            slug = match.group(1)
            worker = TaskWorker(self.api.get_series_info, slug)
            worker.signals.finished.connect(self.show_manga_info)
            self.threadpool.start(worker)

    def show_manga_info(self, manga):
        if not manga: return
        self.current_manga = manga
        
        # Clear old info
        for i in reversed(range(self.manga_layout.count())):
            item = self.manga_layout.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()
            
        # UI for Manga Info
        row1 = QHBoxLayout()
        cover_label = QLabel()
        cover_label.setFixedSize(200, 300)
        cover_label.setScaledContents(True)
        # Load cover again...
        row1.addWidget(cover_label)
        
        details = QVBoxLayout()
        title = QLabel(manga.title)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #00d2ff; margin-bottom: 10px;")
        details.addWidget(title)
        
        meta_layout = QHBoxLayout()
        for label_text in [f"Author: {manga.author}", f"Artist: {manga.artist}", f"Status: {manga.status}", f"Rating: {manga.rating:.2f}"]:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("background: #1a1a2e; border: 1px solid #333344; border-radius: 4px; padding: 5px 10px; color: #00ffaa; font-weight: bold;")
            meta_layout.addWidget(lbl)
        details.addLayout(meta_layout)
        
        genres_lbl = QLabel(f"Genres: {', '.join([g.name for g in manga.genres])}")
        genres_lbl.setStyleSheet("color: #8888aa; margin-top: 10px;")
        genres_lbl.setWordWrap(True)
        details.addWidget(genres_lbl)
        
        desc_lbl = QLabel(re.sub('<[^<]+?>', '', manga.description))
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #8888aa; font-size: 13px; line-height: 1.4;")
        details.addWidget(desc_lbl)
        details.addStretch()
        
        row1.addLayout(details)
        self.manga_layout.addLayout(row1)
        
        # Load Cover asynchronously
        cover_worker = TaskWorker(requests.get, manga.cover, timeout=10)
        def set_cover(res):
            pix = QPixmap()
            pix.loadFromData(res.content)
            cover_label.setPixmap(pix)
        cover_worker.signals.finished.connect(set_cover)
        self.threadpool.start(cover_worker)
        
        # Fetch chapters
        worker = TaskWorker(self.api.get_chapters, manga.slug)
        worker.signals.finished.connect(self.display_chapters)
        self.threadpool.start(worker)
        
        self.switch_tab(2)

    def display_chapters(self, chapters):
        self.chapters = chapters
        
        # Chapter Table
        self.chapter_table = QTableWidget(len(chapters), 3)
        self.chapter_table.setHorizontalHeaderLabels(["Select", "Number", "Title"])
        self.chapter_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.chapter_table.cellClicked.connect(self.toggle_chapter_cb)
        
        header = self.chapter_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            self.chapter_table.setColumnWidth(0, 50)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.chapter_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.chapter_table.setMinimumHeight(400) # Ensure it's big enough

        # Show oldest to newest
        for i, chap in enumerate(chapters):
            cb_item = QTableWidgetItem()
            cb_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            cb_item.setCheckState(Qt.CheckState.Unchecked)
            self.chapter_table.setItem(i, 0, cb_item)
            self.chapter_table.setItem(i, 1, QTableWidgetItem(f"Chapter {chap.number}"))
            self.chapter_table.setItem(i, 2, QTableWidgetItem(chap.title or ""))

        self.manga_layout.addWidget(self.chapter_table)
        
        # Download Controls
        controls = QHBoxLayout()
        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("Range e.g. 1-10, 15 (leave empty for selected above)")
        controls.addWidget(self.range_input)
        
        dl_btn = QPushButton("Download Selected")
        dl_btn.setObjectName("primary_button")
        dl_btn.clicked.connect(self.start_download)
        controls.addWidget(dl_btn)
        
        self.manga_layout.addLayout(controls)

    def toggle_chapter_cb(self, row, column):
        item = self.chapter_table.item(row, 0)
        if item:
            new_state = Qt.CheckState.Checked if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
            item.setCheckState(new_state)

    def start_download(self):
        range_str = self.range_input.text()
        if not range_str:
            # Get selected from checkboxes
            selected = []
            for i in range(self.chapter_table.rowCount()):
                item = self.chapter_table.item(i, 0)
                if item and item.checkState() == Qt.CheckState.Checked:
                    selected.append(self.chapters[i])
            
            if not selected:
                return
                
            worker = TaskWorker(self.download_selected, selected)
        else:
            worker = TaskWorker(self.downloader.download_manga, self.current_manga, range_str, self.progress_bridge, self.progress_bridge)
        
        self.switch_tab(3) # Switch to progress tab
        self.threadpool.start(worker)

    def download_selected(self, chapters):
        overall_task = self.progress_bridge.add_task("[Total Progress]", total=len(chapters))
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=self.config_mgr.settings.threads_chapters) as executor:
            futures = []
            for chap in chapters:
                def run_chap(c=chap):
                    series_slug = c.series_slug or self.current_manga.slug
                    pages = self.api.get_chapter_images(series_slug, c.slug)
                    task_id = self.progress_bridge.add_task(f"Chapter {c.number}", total=len(pages))
                    
                    self.downloader.download_chapter(
                        self.current_manga, 
                        c, 
                        series_slug, 
                        lambda n: self.progress_bridge.update(task_id, advance=n)
                    )
                    self.progress_bridge.update(overall_task, advance=1)
                    self.progress_bridge.remove_task(task_id)

                futures.append(executor.submit(run_chap))
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Chapter download error: {e}")

    def on_task_added(self, task_id, name, total):
        row = self.progress_table.rowCount()
        self.progress_table.insertRow(row)
        
        self.progress_table.setItem(row, 0, QTableWidgetItem(name))
        
        status_item = QTableWidgetItem("Downloading...")
        self.progress_table.setItem(row, 1, status_item)
        
        progress_bar = QProgressBar()
        progress_bar.setMaximum(total)
        progress_bar.setValue(0)
        progress_bar.setFormat("%v/%m (%p%)")
        self.progress_table.setCellWidget(row, 2, progress_bar)
        
        self.task_id_to_row[task_id] = row

    def on_task_updated(self, task_id, advance):
        row = self.task_id_to_row.get(task_id)
        if row is not None:
            widget = self.progress_table.cellWidget(row, 2)
            if isinstance(widget, QProgressBar):
                widget.setValue(widget.value() + advance)
                if widget.value() >= widget.maximum():
                    item = self.progress_table.item(row, 1)
                    if item:
                        item.setText("Finished")

    def on_task_removed(self, task_id):
        pass # Optional: remove from table or just keep as "Finished"
