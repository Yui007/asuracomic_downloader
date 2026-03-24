from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.config_manager import ConfigManager
import sys

def main():
    app = QApplication(sys.argv)
    config_mgr = ConfigManager()
    
    window = MainWindow(config_mgr)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
