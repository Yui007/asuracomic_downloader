from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
import requests
from io import BytesIO

class GlassCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glass_card")
        self.main_layout = None

class MangaCard(GlassCard):
    clicked = pyqtSignal(object)

    def __init__(self, manga, parent=None):
        super().__init__(parent)
        self.manga = manga
        self.main_layout = QVBoxLayout(self)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(140, 200)
        self.cover_label.setScaledContents(True)
        self.cover_label.setStyleSheet("border-radius: 8px;")
        
        self.title_label = QLabel(manga.title)
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("manga_title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.main_layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addStretch()
        
        self.load_cover(manga.cover)

    def load_cover(self, url):
        # We should ideally do this in a thread, but for now...
        try:
            res = requests.get(url, timeout=5)
            pix = QPixmap()
            pix.loadFromData(res.content)
            self.cover_label.setPixmap(pix)
        except:
            pass

    def mousePressEvent(self, a0):
        self.clicked.emit(self.manga)
        super().mousePressEvent(a0)
