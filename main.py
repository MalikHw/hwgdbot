import sys
import json
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox, QCheckBox, QVBoxLayout, QDialog, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from main_window import MainWindow

class DonationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Support HwGDBot")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        msg = QLabel("Hey! I've spent a lot of time making HwGDBot free for everyone.\n\n"
                    "If you find it useful, please consider supporting me!\n"
                    "Every donation helps keep this project alive. ❤️")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        
        self.dont_show = QCheckBox("Don't show this again")
        layout.addWidget(self.dont_show, alignment=Qt.AlignmentFlag.AlignCenter)
        
        donate_btn = QPushButton("💝 Donate Now")
        donate_btn.clicked.connect(self.open_donate)
        donate_btn.setStyleSheet("QPushButton { background-color: #ff4444; color: white; font-weight: bold; padding: 10px; }")
        layout.addWidget(donate_btn)
        
        close_btn = QPushButton("Maybe Later")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def open_donate(self):
        import webbrowser
        webbrowser.open("https://malikhw.github.io/donate")
        self.accept()

def main():
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("HwGDBot")
    app.setOrganizationName("MalikHw")
    
    # Load settings
    settings_file = data_dir / "settings.json"
    settings = {}
    if settings_file.exists():
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    
    # Show donation popup if not disabled
    if not settings.get('hide_donation_popup', False):
        dialog = DonationDialog()
        dialog.exec()
        
        if dialog.dont_show.isChecked():
            settings['hide_donation_popup'] = True
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
    
    # Set icon if available
    icon_path = Path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
