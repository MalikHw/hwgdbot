import sys
import json
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox, QCheckBox, QVBoxLayout, QDialog, QPushButton, QLabel, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap
from main_window import MainWindow

# Setup logging
logging.basicConfig(
    filename='log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
        self.accept()
        self.parent().open_donate_page()

class FirstRunDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HwGDBot - Premium Features")
        self.setModal(True)
        self.setFixedSize(500, 300)
        self.stage = 1
        
        self.layout = QVBoxLayout()
        
        self.msg = QLabel("⚠️ NOTICE ⚠️\n\n"
                         "Most features in HwGDBot are PAID and require a license!\n\n"
                         "Premium features include:\n"
                         "• Queue management\n"
                         "• OBS overlay\n"
                         "• Automod system\n"
                         "• Cloud backups\n\n"
                         "Purchase a license to unlock full access.")
        self.msg.setWordWrap(True)
        self.msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg.setStyleSheet("font-size: 14px;")
        self.layout.addWidget(self.msg)
        
        btn_layout = QVBoxLayout()
        
        self.deny1_btn = QPushButton("❌ I can't afford it")
        self.deny1_btn.clicked.connect(self.show_joke)
        self.deny1_btn.setStyleSheet("QPushButton { background-color: #666; color: white; padding: 10px; }")
        btn_layout.addWidget(self.deny1_btn)
        
        self.deny2_btn = QPushButton("❌ This is ridiculous")
        self.deny2_btn.clicked.connect(self.show_joke)
        self.deny2_btn.setStyleSheet("QPushButton { background-color: #666; color: white; padding: 10px; }")
        btn_layout.addWidget(self.deny2_btn)
        
        self.layout.addLayout(btn_layout)
        self.setLayout(self.layout)
    
    def show_joke(self):
        self.msg.setText("😂 I'm kidding!\n\n"
                        "HwGDBot is totally FREE and always will be!\n\n"
                        "No premium features, no licenses, no Bullshit.\n"
                        "Just a tool made by a streamer, for streamers.\n\n"
                        "Enjoy! ❤️")
        
        # Remove old buttons
        self.deny1_btn.setParent(None)
        self.deny2_btn.setParent(None)
        
        # Add new button
        scared_btn = QPushButton("😨 You scared me! 🥀")
        scared_btn.clicked.connect(self.accept)
        scared_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        self.layout.addWidget(scared_btn)

def exception_hook(exctype, value, tb):
    """Global exception handler"""
    logging.exception("Uncaught exception", exc_info=(exctype, value, tb))
    
    # Try to restore queue
    try:
        from pathlib import Path
        data_dir = Path("data")
        queue_file = data_dir / "queue.json"
        
        if queue_file.exists():
            import shutil
            backup_file = data_dir / f"queue_crash_backup_{int(time.time())}.json"
            shutil.copy(queue_file, backup_file)
            logging.info(f"Queue backed up to {backup_file}")
    except:
        pass
    
    # Show error dialog
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("HwGDBot Crashed")
    msg.setText("HwGDBot encountered an error and needs to close.")
    msg.setInformativeText(f"Error: {value}\n\n"
                          f"A log file (log.txt) has been created.\n"
                          f"Please report this to 'malikhw' on Discord!")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()
    
    sys.__excepthook__(exctype, value, tb)

def main():
    # Set global exception hook
    sys.excepthook = exception_hook
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("HwGDBot")
    app.setOrganizationName("MalikHw")
    
    # Show splash screen
    icon_path = Path("icon.png")
    if icon_path.exists():
        splash_pix = QPixmap(str(icon_path))
        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        splash.show()
        app.processEvents()
        QTimer.singleShot(1500, splash.close)  # Show for 1.5s
    
    # Set icon if available
    icon_path = Path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    elif Path("icon.png").exists():
        app.setWindowIcon(QIcon("icon.png"))
    
    # Load settings
    settings_file = data_dir / "settings.json"
    settings = {}
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except:
            logging.exception("Failed to load settings")
            settings = {}
    
    # Check if first run
    is_first_run = not settings.get('first_run_completed', False)
    
    if is_first_run:
        # Show joke dialog
        joke_dialog = FirstRunDialog()
        joke_dialog.exec()
        
        settings['first_run_completed'] = True
    
    # Show donation popup if not disabled
    if not settings.get('hide_donation_popup', False):
        window_temp = MainWindow()  # Temporary for donate method
        dialog = DonationDialog(window_temp)
        dialog.exec()
        
        if dialog.dont_show.isChecked():
            settings['hide_donation_popup'] = True
        
        # Save settings
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    
    window = MainWindow()
    
    # Animate settings button on first run
    if is_first_run:
        QTimer.singleShot(2000, lambda: animate_settings_button(window))
    
    window.show()
    
    sys.exit(app.exec())

def animate_settings_button(window):
    """Zoom in/out animation for settings button"""
    btn = window.btn_settings
    original_style = btn.styleSheet()
    
    def zoom_in():
        btn.setStyleSheet(original_style + "QPushButton { font-size: 18px; }")
    
    def zoom_out():
        btn.setStyleSheet(original_style + "QPushButton { font-size: 14px; }")
    
    def reset():
        btn.setStyleSheet(original_style)
    
    # Animate 3 times
    for i in range(3):
        QTimer.singleShot(i * 600, zoom_in)
        QTimer.singleShot(i * 600 + 300, zoom_out)
    
    QTimer.singleShot(1800, reset)

if __name__ == "__main__":
    import time
    main()
