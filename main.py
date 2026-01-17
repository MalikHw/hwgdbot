import sys
import os
import json
import traceback
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from main_window import MainWindow
from notification_service import NotificationService
from update_checker import UpdateChecker

VERSION = "1.0.0"
DATA_DIR = "data"
LOG_FILE = "log.txt"

def log(level, message):
    """Log message to log.txt with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Failed to write log: {e}")

def exception_handler(exc_type, exc_value, exc_traceback):
    """Global exception handler for crash recovery"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log("CRITICAL", f"Unhandled exception:\n{error_msg}")
    
    # Backup queue on crash
    try:
        queue_path = os.path.join(DATA_DIR, "queue.json")
        if os.path.exists(queue_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(DATA_DIR, f"queue_crash_backup_{timestamp}.json")
            with open(queue_path, "r", encoding="utf-8") as src:
                with open(backup_path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
            log("INFO", f"Created crash backup: {backup_path}")
    except Exception as e:
        log("ERROR", f"Failed to create crash backup: {e}")
    
    # Show error dialog
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle("HwGDBot Crashed")
    msg.setText("HwGDBot crashed unexpectedly!")
    msg.setInformativeText(f"Please report log.txt to 'malikhw' on Discord.\n\nError: {exc_value}")
    msg.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg.exec()

class FirstRunDialog(QDialog):
    """Joke premium dialog on first run"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Premium Features Required")
        self.setFixedSize(400, 200)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("HwGDBot requires a premium subscription to continue.\n\nPlease purchase a license for $99.99/month.")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        
        self.deny1 = QPushButton("DENY")
        self.deny1.clicked.connect(self.show_second_deny)
        layout.addWidget(self.deny1)
        
        self.deny2 = QPushButton("DENY")
        self.deny2.clicked.connect(self.show_joke_reveal)
        self.deny2.hide()
        layout.addWidget(self.deny2)
        
        self.reveal_label = QLabel("Just kidding! It's totally free!")
        self.reveal_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reveal_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
        self.reveal_label.hide()
        layout.addWidget(self.reveal_label)
        
        self.ok_button = QPushButton("You scared me")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.hide()
        layout.addWidget(self.ok_button)
        
        self.setLayout(layout)
    
    def show_second_deny(self):
        self.deny1.hide()
        self.deny2.show()
    
    def show_joke_reveal(self):
        self.label.hide()
        self.deny2.hide()
        self.reveal_label.show()
        self.ok_button.show()

class DonationDialog(QDialog):
    """Donation popup with 'Don't show again' option"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Support HwGDBot")
        self.setFixedSize(400, 200)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        label = QLabel("Hey! If you like HwGDBot, consider supporting the developer.\n\nYour support helps keep this project alive!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        donate_btn = QPushButton("Donate")
        donate_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold; padding: 10px;")
        donate_btn.clicked.connect(self.open_donation_page)
        layout.addWidget(donate_btn)
        
        self.dont_show_cb = QCheckBox("Don't show again")
        layout.addWidget(self.dont_show_cb)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def open_donation_page(self):
        import webbrowser
        webbrowser.open("https://malikhw.github.io/donate")

def ensure_data_folder():
    """Create data folder if it doesn't exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        log("INFO", "Created data folder")

def load_settings():
    """Load settings or create default"""
    settings_path = os.path.join(DATA_DIR, "settings.json")
    default_settings = {
        "first_run": True,
        "show_donation_popup": True,
        "twitch_token": "",
        "twitch_username": "",
        "youtube_enabled": False,
        "post_command": "!post",
        "delete_command": "!del",
        "max_ids_per_user": 0,
        "per_user_cooldown": True,
        "block_same_level_same_user": True,
        "reject_fucked_list": True,
        "ignore_played": True,
        "length_filters": {
            "tiny": True,
            "short": True,
            "medium": True,
            "long": True,
            "xl": True
        },
        "difficulty_filters": {
            "auto": True,
            "easy": True,
            "normal": True,
            "hard": True,
            "harder": True,
            "insane": True,
            "demon-easy": True,
            "demon-medium": True,
            "demon-hard": True,
            "demon-insane": True,
            "demon-extreme": True
        },
        "block_disliked": False,
        "rated_filter": "Any",
        "block_large": False,
        "save_queue_on_change": True,
        "load_queue_on_start": True,
        "obs_overlay_enabled": False,
        "obs_overlay_window_enabled": False,
        "obs_overlay_template": "{level} by {author} (ID: {id})",
        "obs_overlay_font": "",
        "obs_overlay_width": 800,
        "obs_overlay_height": 100,
        "obs_overlay_transparency": 100,
        "sounds_enabled": False,
        "sound_new_level": "",
        "sound_error": "",
        "backup_enabled": False,
        "backup_interval": 10,
        "streamer_name": ""
    }
    
    try:
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key in default_settings:
                    if key not in loaded:
                        loaded[key] = default_settings[key]
                return loaded
        else:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, indent=2)
            log("INFO", "Created default settings.json")
            return default_settings
    except Exception as e:
        log("ERROR", f"Failed to load settings: {e}")
        return default_settings

def save_settings(settings):
    """Save settings to file"""
    settings_path = os.path.join(DATA_DIR, "settings.json")
    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        log("INFO", "Settings saved")
    except Exception as e:
        log("ERROR", f"Failed to save settings: {e}")

def main():
    # Set up global exception handler
    sys.excepthook = exception_handler
    
    # Initialize logging
    log("INFO", f"HwGDBot v{VERSION} starting")
    
    # Ensure data folder exists
    ensure_data_folder()
    
    # Load settings
    settings = load_settings()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("HwGDBot")
    app.setApplicationVersion(VERSION)
    
    # Show splash screen
    if os.path.exists("icon.png"):
        splash_pix = QPixmap("icon.png")
        splash = QSplashScreen(splash_pix)
        splash.show()
        app.processEvents()
        
        # Keep splash for 1.5 seconds
        QTimer.singleShot(1500, splash.close)
        QTimer.singleShot(1500, lambda: show_main_app(app, settings))
    else:
        show_main_app(app, settings)
    
    sys.exit(app.exec())

def show_main_app(app, settings):
    """Show main application after splash"""
    # First run dialog
    if settings.get("first_run", True):
        first_run = FirstRunDialog()
        first_run.exec()
        settings["first_run"] = False
        save_settings(settings)
        log("INFO", "First run completed")
    
    # Donation popup
    if settings.get("show_donation_popup", True):
        donation = DonationDialog()
        donation.exec()
        if donation.dont_show_cb.isChecked():
            settings["show_donation_popup"] = False
            save_settings(settings)
        log("INFO", "Donation dialog shown")
    
    # Create and show main window
    main_window = MainWindow(settings)
    main_window.show()
    
    # Animate settings button on first run (after donation dialog)
    if settings.get("first_run") is False and settings.get("show_donation_popup", True):
        QTimer.singleShot(500, main_window.animate_settings_button)
    
    # Check for updates
    update_checker = UpdateChecker(VERSION)
    update_checker.check_for_updates()
    
    log("INFO", "Main window shown")

if __name__ == "__main__":
    main()