from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QStatusBar, QSystemTrayIcon, 
                             QMenu, QMessageBox, QListWidgetItem, QTextEdit, QInputDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QAction
from pathlib import Path
import json
import webbrowser
import zipfile
import os
from datetime import datetime

from settings_window import SettingsWindow
from queue_manager import QueueManager
from twitch_service import TwitchService
from youtube_service import YouTubeService
from gd_integration import GDIntegration
from automod_service import AutomodService
from obs_overlay import OBSOverlay
from notification_service import NotificationService
from update_checker import UpdateChecker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HwGDBot - Queue Manager")
        self.resize(900, 600)
        
        self.data_dir = Path("data")
        self.queue_manager = QueueManager(self.data_dir)
        self.gd_integration = GDIntegration(self.data_dir)
        self.automod = AutomodService(self.data_dir)
        self.notification = NotificationService()
        
        # Services
        self.twitch_service = None
        self.youtube_service = None
        self.obs_overlay = None
        
        # Backup timer
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.perform_auto_backup)
        
        self.setup_ui()
        self.setup_tray()
        self.load_settings()
        self.setup_backup_timer()
        self.check_for_updates()
        
        # Connect to chat services
        QTimer.singleShot(500, self.connect_services)
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # Left side - Queue list
        left_layout = QVBoxLayout()
        
        queue_label = QLabel("Level Queue")
        queue_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(queue_label)
        
        self.queue_list = QListWidget()
        self.queue_list.itemClicked.connect(self.on_queue_item_selected)
        left_layout.addWidget(self.queue_list)
        
        main_layout.addLayout(left_layout, 2)
        
        # Right side - Level info and controls
        right_layout = QVBoxLayout()
        
        self.level_info = QTextEdit()
        self.level_info.setReadOnly(True)
        self.level_info.setMaximumHeight(250)
        right_layout.addWidget(QLabel("Level Details"))
        right_layout.addWidget(self.level_info)
        
        # Action buttons
        btn_layout = QVBoxLayout()
        
        self.btn_copy = QPushButton("📋 Copy ID")
        self.btn_copy.clicked.connect(self.copy_level_id)
        btn_layout.addWidget(self.btn_copy)
        
        self.btn_skip = QPushButton("⏭️ Skip")
        self.btn_skip.clicked.connect(self.skip_level)
        btn_layout.addWidget(self.btn_skip)
        
        self.btn_played = QPushButton("✅ Mark Played")
        self.btn_played.clicked.connect(self.mark_played)
        btn_layout.addWidget(self.btn_played)
        
        self.btn_report = QPushButton("🚨 Report")
        self.btn_report.clicked.connect(self.report_level)
        btn_layout.addWidget(self.btn_report)
        
        btn_layout.addWidget(QLabel("Blacklist Actions:"))
        
        self.btn_ban_requester = QPushButton("🚫 Ban Requester")
        self.btn_ban_requester.clicked.connect(self.ban_requester)
        btn_layout.addWidget(self.btn_ban_requester)
        
        self.btn_ban_creator = QPushButton("🚫 Ban Creator")
        self.btn_ban_creator.clicked.connect(self.ban_creator)
        btn_layout.addWidget(self.btn_ban_creator)
        
        self.btn_ban_id = QPushButton("🚫 Ban Level ID")
        self.btn_ban_id.clicked.connect(self.ban_level_id)
        btn_layout.addWidget(self.btn_ban_id)
        
        btn_layout.addStretch()
        
        self.btn_settings = QPushButton("⚙️ Settings")
        self.btn_settings.clicked.connect(self.open_settings)
        btn_layout.addWidget(self.btn_settings)
        
        right_layout.addLayout(btn_layout)
        main_layout.addLayout(right_layout, 1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Disconnected")
        
        self.update_queue_display()
    
    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon_path = Path("icon.ico")
        if icon_path.exists():
            self.tray.setIcon(QIcon(str(icon_path)))
        
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()
    
    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage("HwGDBot", "App minimized to tray", QSystemTrayIcon.MessageIcon.Information, 2000)
    
    def quit_app(self):
        if self.twitch_service:
            self.twitch_service.stop()
        if self.youtube_service:
            self.youtube_service.stop()
        QApplication.quit()
    
    def load_settings(self):
        settings_file = self.data_dir / "settings.json"
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        else:
            self.settings = {}
    
    def connect_services(self):
        # Start Twitch service
        twitch_token = self.settings.get('twitch_token')
        twitch_channel = self.settings.get('twitch_channel')
        
        if twitch_token and twitch_channel:
            self.twitch_service = TwitchService(twitch_token, twitch_channel)
            self.twitch_service.level_requested.connect(self.handle_level_request)
            self.twitch_service.connection_status.connect(self.update_status)
            self.twitch_service.start()
        
        # Ask for YouTube livestream URL
        if self.settings.get('enable_youtube', False):
            from youtube_dialog import YouTubeDialog
            dialog = YouTubeDialog(self)
            if dialog.exec():
                url = dialog.url_input.text().strip()
                if url:
                    self.youtube_service = YouTubeService(url)
                    self.youtube_service.level_requested.connect(self.handle_level_request)
                    self.youtube_service.start()
        
        # Start OBS overlay if enabled
        if self.settings.get('enable_obs_overlay', False):
            self.obs_overlay = OBSOverlay(self.queue_manager, self.settings)
            self.obs_overlay.show()
    
    def handle_level_request(self, level_id, requester, platform):
        # Run automod checks
        result = self.automod.check_level(level_id, requester, platform)
        
        if not result['allowed']:
            self.notification.show_error(f"Blocked: {result['reason']}")
            return
        
        # Fetch level data
        level_data = self.gd_integration.fetch_level(level_id)
        
        if not level_data:
            self.notification.show_error(f"Failed to fetch level {level_id}")
            return
        
        # Add to queue
        level_data['requester'] = requester
        level_data['platform'] = platform
        
        if self.queue_manager.add_level(level_data):
            self.notification.show_success(f"Added: {level_data['level_name']}")
            self.update_queue_display()
            if self.obs_overlay:
                self.obs_overlay.update_display()
        else:
            self.notification.show_warning(f"Level already in queue")
    
    def update_queue_display(self):
        self.queue_list.clear()
        queue = self.queue_manager.get_queue()
        
        for level in queue:
            item = QListWidgetItem()
            
            # Load difficulty icon
            diff = level.get('difficulty', 'auto').lower()
            icon_path = Path(f"icons/{diff}.png")
            if icon_path.exists():
                item.setIcon(QIcon(str(icon_path)))
            
            item.setText(f"{level['level_name']} by {level['author']}")
            item.setData(Qt.ItemDataRole.UserRole, level)
            
            # Tooltip with full info
            tooltip = f"ID: {level['level_id']}\n"
            tooltip += f"Author: {level['author']}\n"
            tooltip += f"Song: {level['song']}\n"
            tooltip += f"Difficulty: {level['difficulty']}\n"
            tooltip += f"Requested by: {level['requester']} ({level.get('platform', 'unknown')})"
            item.setToolTip(tooltip)
            
            self.queue_list.addItem(item)
    
    def on_queue_item_selected(self, item):
        level = item.data(Qt.ItemDataRole.UserRole)
        
        info = f"<b>Level:</b> {level['level_name']}<br>"
        info += f"<b>ID:</b> {level['level_id']}<br>"
        info += f"<b>Author:</b> {level['author']}<br>"
        info += f"<b>Song:</b> {level['song']}<br>"
        info += f"<b>Difficulty:</b> {level['difficulty']}<br>"
        info += f"<b>Downloads:</b> {level.get('downloads', 'N/A')}<br>"
        info += f"<b>Likes:</b> {level.get('likes', 'N/A')}<br>"
        info += f"<b>Requested by:</b> {level['requester']} ({level.get('platform', 'unknown')})<br>"
        info += f"<b>Attempts:</b> {level.get('attempts', 0)}"
        
        self.level_info.setHtml(info)
    
    def copy_level_id(self):
        item = self.queue_list.currentItem()
        if item:
            level = item.data(Qt.ItemDataRole.UserRole)
            QApplication.clipboard().setText(str(level['level_id']))
            self.notification.show_success("Level ID copied!")
    
    def skip_level(self):
        item = self.queue_list.currentItem()
        if item:
            level = item.data(Qt.ItemDataRole.UserRole)
            self.queue_manager.remove_level(level['level_id'])
            self.update_queue_display()
            if self.obs_overlay:
                self.obs_overlay.update_display()
    
    def mark_played(self):
        item = self.queue_list.currentItem()
        if item:
            level = item.data(Qt.ItemDataRole.UserRole)
            self.queue_manager.mark_played(level['level_id'])
            self.queue_manager.remove_level(level['level_id'])
            self.update_queue_display()
            if self.obs_overlay:
                self.obs_overlay.update_display()
            self.notification.show_success("Level marked as played!")
    
    def report_level(self):
        item = self.queue_list.currentItem()
        if item:
            level = item.data(Qt.ItemDataRole.UserRole)
            reason, ok = QInputDialog.getText(self, "Report Level", "Reason for report:")
            
            if ok and reason:
                import requests
                try:
                    requests.post("https://hwgdbot.rf.gd/fuckit.php", json={
                        'level_id': level['level_id'],
                        'level_name': level['level_name'],
                        'author': level['author'],
                        'reason': reason,
                        'reporter': self.settings.get('twitch_channel', 'unknown')
                    }, timeout=5)
                    self.notification.show_success("Report submitted!")
                except:
                    self.notification.show_error("Failed to submit report")
    
    def ban_requester(self):
        item = self.queue_list.currentItem()
        if item:
            level = item.data(Qt.ItemDataRole.UserRole)
            self.automod.add_to_blacklist('requester', level['requester'])
            self.notification.show_success(f"Banned requester: {level['requester']}")
    
    def ban_creator(self):
        item = self.queue_list.currentItem()
        if item:
            level = item.data(Qt.ItemDataRole.UserRole)
            self.automod.add_to_blacklist('creator', level['author'])
            self.notification.show_success(f"Banned creator: {level['author']}")
    
    def ban_level_id(self):
        item = self.queue_list.currentItem()
        if item:
            level = item.data(Qt.ItemDataRole.UserRole)
            self.automod.add_to_blacklist('id', level['level_id'])
            self.notification.show_success(f"Banned level ID: {level['level_id']}")
    
    def open_settings(self):
        dialog = SettingsWindow(self.settings, self.data_dir, self)
        if dialog.exec():
            self.settings = dialog.get_settings()
            # Update backup timer
            self.setup_backup_timer()
            # Restart services if needed
            self.connect_services()
    
    def setup_backup_timer(self):
        """Setup automatic backup timer based on settings"""
        self.backup_timer.stop()
        
        if self.settings.get('backup_enable', False):
            interval_minutes = self.settings.get('backup_interval', 10)
            interval_ms = interval_minutes * 60 * 1000
            self.backup_timer.start(interval_ms)
    
    def perform_auto_backup(self):
        """Perform automatic backup"""
        try:
            # Get Documents folder path based on OS
            if os.name == 'nt':  # Windows
                docs_path = Path(os.path.expanduser('~')) / 'Documents'
            else:  # Linux/macOS
                docs_path = Path(os.path.expanduser('~')) / 'Documents'
            
            backup_dir = docs_path / 'HwGDBot'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            backup_file = backup_dir / f'backup-{timestamp}.hgb-bkp'
            
            # Create zip file
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all JSON files from data directory
                for file in ['queue.json', 'played.json', 'settings.json', 
                            'blacklist_requesters.json', 'blacklist_creators.json', 
                            'blacklist_ids.json', 'cache.json']:
                    file_path = self.data_dir / file
                    if file_path.exists():
                        zipf.write(file_path, file)
            
            # Keep only last 10 backups
            backups = sorted(backup_dir.glob('backup-*.hgb-bkp'))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
            
            self.status_bar.showMessage(f"Auto-backup saved: {timestamp}", 5000)
        
        except Exception as e:
            print(f"Auto-backup failed: {e}")
    
    def update_status(self, status):
        self.status_bar.showMessage(status)
    
    def check_for_updates(self):
        checker = UpdateChecker()
        if checker.has_update():
            reply = QMessageBox.question(self, "Update Available", 
                                        f"New version {checker.latest_version} is available!\n\nDownload now?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open("https://malikhw.github.io/HwGDBot")
