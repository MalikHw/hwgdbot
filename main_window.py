import os
import json
import webbrowser
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QListWidget, QListWidgetItem, QPushButton, QCheckBox,
                             QLabel, QTextEdit, QMessageBox, QMenu, QSystemTrayIcon, QApplication)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QPixmap, QAction
from settings_window import SettingsWindow
from queue_manager import QueueManager
from twitch_service import TwitchService
from youtube_service import YouTubeService
from automod_service import AutomodService
from obs_overlay import OBSOverlay
from notification_service import NotificationService
from youtube_dialog import YouTubeDialog
from backup_service import BackupService

class MainWindow(QMainWindow):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.queue_manager = None
        self.twitch_service = None
        self.youtube_service = None
        self.automod_service = None
        self.obs_overlay = None
        self.notification_service = None
        self.system_tray = None
        self.backup_service = None
        self.backup_timer = None
        
        self.init_ui()
        self.init_services()
        self.setup_system_tray()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("HwGDBot")
        self.setGeometry(100, 100, 1000, 600)
        
        # Set window icon
        if os.path.exists("icon.png"):
            self.setWindowIcon(QIcon("icon.png"))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left side - Queue list
        left_layout = QVBoxLayout()
        
        # Accept requests toggle
        self.accept_toggle = QCheckBox("Accept Requests")
        self.accept_toggle.setChecked(True)
        self.accept_toggle.stateChanged.connect(self.toggle_accept_requests)
        left_layout.addWidget(self.accept_toggle)
        
        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.currentItemChanged.connect(self.on_queue_selection_changed)
        left_layout.addWidget(self.queue_list)
        
        main_layout.addLayout(left_layout, 2)
        
        # Right side - Level info and controls
        right_layout = QVBoxLayout()
        
        # Level info panel
        info_label = QLabel("Level Information")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(info_label)
        
        self.level_info = QTextEdit()
        self.level_info.setReadOnly(True)
        self.level_info.setMaximumHeight(200)
        right_layout.addWidget(self.level_info)
        
        # Control buttons
        btn_layout = QVBoxLayout()
        
        self.copy_id_btn = QPushButton("Copy ID")
        self.copy_id_btn.clicked.connect(self.copy_id)
        btn_layout.addWidget(self.copy_id_btn)
        
        self.skip_btn = QPushButton("Skip")
        self.skip_btn.clicked.connect(self.skip_level)
        btn_layout.addWidget(self.skip_btn)
        
        self.mark_played_btn = QPushButton("Mark Played")
        self.mark_played_btn.clicked.connect(self.mark_played)
        btn_layout.addWidget(self.mark_played_btn)
        
        self.report_btn = QPushButton("Report")
        self.report_btn.clicked.connect(self.report_level)
        btn_layout.addWidget(self.report_btn)
        
        self.ban_requester_btn = QPushButton("Ban Requester")
        self.ban_requester_btn.clicked.connect(self.ban_requester)
        btn_layout.addWidget(self.ban_requester_btn)
        
        self.ban_creator_btn = QPushButton("Ban Creator")
        self.ban_creator_btn.clicked.connect(self.ban_creator)
        btn_layout.addWidget(self.ban_creator_btn)
        
        self.ban_id_btn = QPushButton("Ban ID")
        self.ban_id_btn.clicked.connect(self.ban_id)
        btn_layout.addWidget(self.ban_id_btn)
        
        right_layout.addLayout(btn_layout)
        
        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        right_layout.addWidget(self.settings_btn)
        
        # Donate button
        donate_btn = QPushButton("Donate")
        donate_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
        donate_btn.clicked.connect(self.open_donate)
        right_layout.addWidget(donate_btn)
        
        right_layout.addStretch()
        
        main_layout.addLayout(right_layout, 1)
        
        # Status bar
        self.statusBar().showMessage("Disconnected")
        
        # Disable buttons initially
        self.update_button_states()
    
    def init_services(self):
        """Initialize all services"""
        from main import log
        
        # Queue manager
        self.queue_manager = QueueManager(self.settings)
        self.queue_manager.queue_changed.connect(self.update_queue_display)
        self.queue_manager.load_queue()
        
        # Automod service
        self.automod_service = AutomodService(self.settings)
        
        # Twitch service
        if self.settings.get("twitch_token") and self.settings.get("twitch_username"):
            self.twitch_service = TwitchService(self.settings)
            self.twitch_service.level_requested.connect(self.handle_level_request)
            self.twitch_service.delete_requested.connect(self.handle_delete_request)
            self.twitch_service.connection_changed.connect(self.update_connection_status)
            self.twitch_service.start()
            log("INFO", "Twitch service started")
        
        # YouTube service
        if self.settings.get("youtube_enabled"):
            dialog = YouTubeDialog()
            if dialog.exec():
                url = dialog.get_url()
                if url:
                    self.youtube_service = YouTubeService(self.settings, url)
                    self.youtube_service.level_requested.connect(self.handle_level_request)
                    self.youtube_service.delete_requested.connect(self.handle_delete_request)
                    self.youtube_service.connection_changed.connect(self.update_connection_status)
                    self.youtube_service.start()
                    log("INFO", "YouTube service started")
        
        # OBS overlay
        if self.settings.get("obs_overlay_enabled"):
            self.obs_overlay = OBSOverlay(self.settings)
            self.queue_manager.queue_changed.connect(self.update_obs_overlay)
            log("INFO", "OBS overlay started")
        
        # Notification service
        self.notification_service = NotificationService(self.settings)
        
        # Backup service
        self.backup_service = BackupService()
        if self.settings.get("backup_enabled", False):
            self.start_backup_timer()
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.system_tray = QSystemTrayIcon(self)
        if os.path.exists("icon.png"):
            self.system_tray.setIcon(QIcon("icon.png"))
        
        # Tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.system_tray.setContextMenu(tray_menu)
        self.system_tray.activated.connect(self.tray_icon_activated)
        self.system_tray.show()
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.system_tray and self.system_tray.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_application()
            event.accept()
    
    def start_backup_timer(self):
        """Start automatic backup timer"""
        if self.backup_timer:
            self.backup_timer.stop()
        
        interval = self.settings.get("backup_interval", 10) * 60 * 1000  # Convert to ms
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self.auto_backup)
        self.backup_timer.start(interval)
        
        from main import log
        log("INFO", f"Backup timer started ({self.settings.get('backup_interval', 10)} minutes)")
    
    def auto_backup(self):
        """Perform automatic backup"""
        if self.backup_service:
            self.backup_service.create_backup()
    
    def quit_application(self):
        """Clean shutdown"""
        from main import log
        
        # Stop services
        if self.twitch_service:
            self.twitch_service.stop()
        if self.youtube_service:
            self.youtube_service.stop()
        if self.obs_overlay:
            self.obs_overlay.close()
        
        # Save queue
        if self.queue_manager:
            self.queue_manager.save_queue()
        
        log("INFO", "Application closed")
        QApplication.quit()
    
    def animate_settings_button(self):
        """Animate settings button to guide user (first run)"""
        animation = QPropertyAnimation(self.settings_btn, b"geometry")
        animation.setDuration(300)
        animation.setLoopCount(3)
        
        original_geo = self.settings_btn.geometry()
        enlarged_geo = original_geo.adjusted(-10, -10, 10, 10)
        
        animation.setStartValue(original_geo)
        animation.setKeyValueAt(0.5, enlarged_geo)
        animation.setEndValue(original_geo)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        animation.start()
    
    def toggle_accept_requests(self, state):
        """Toggle accepting new requests"""
        accepting = state == Qt.CheckState.Checked.value
        self.queue_manager.set_accepting(accepting)
        status = "Accepting requests" if accepting else "Paused"
        self.statusBar().showMessage(f"{self.get_connection_status()} - {status}")
    
    def update_queue_display(self):
        """Update the queue list display"""
        self.queue_list.clear()
        
        for level in self.queue_manager.get_queue():
            item = QListWidgetItem()
            
            # Get difficulty icon
            difficulty = level.get("difficulty", "auto")
            if "demon" in difficulty:
                icon_name = "demon.png"
            elif difficulty == "unrated":
                icon_name = "unrated.png"
            else:
                icon_name = f"{difficulty}.png"
            
            icon_path = os.path.join("icons", icon_name)
            if os.path.exists(icon_path):
                item.setIcon(QIcon(icon_path))
            
            # Build display text
            display_text = f"{level['level_name']} - {level['author']} ({level['requester']} - {level['level_id']})"
            
            # Add star for rated
            if level.get("is_rated"):
                display_text = "⭐ " + display_text
            
            # Add (+) for large
            if level.get("is_large"):
                display_text += " (+)"
            
            # Add WARNING for fucked levels
            if level.get("is_fucked"):
                display_text += " ⚠️ WARNING"
            
            item.setText(display_text)
            
            # Tooltip with full info
            tooltip = f"ID: {level['level_id']}\n"
            tooltip += f"Name: {level['level_name']}\n"
            tooltip += f"Author: {level['author']}\n"
            tooltip += f"Song: {level.get('song', 'N/A')}\n"
            tooltip += f"Difficulty: {level['difficulty']}\n"
            tooltip += f"Length: {level['length']}\n"
            tooltip += f"Rated: {'Yes' if level.get('is_rated') else 'No'}\n"
            tooltip += f"Large: {'Yes' if level.get('is_large') else 'No'}\n"
            tooltip += f"Requester: {level['requester']} ({level['platform']})\n"
            tooltip += f"Attempts: {level.get('attempts', 0)}"
            
            if level.get("is_fucked"):
                tooltip += f"\n\n⚠️ WARNING: This level is flagged - don't play on stream!"
                if level.get("fucked_note"):
                    tooltip += f"\nReason: {level['fucked_note']}"
            
            item.setToolTip(tooltip)
            item.setData(Qt.ItemDataRole.UserRole, level)
            
            self.queue_list.addItem(item)
        
        self.update_button_states()
    
    def on_queue_selection_changed(self, current, previous):
        """Handle queue selection change"""
        if current:
            level = current.data(Qt.ItemDataRole.UserRole)
            self.display_level_info(level)
        else:
            self.level_info.clear()
        
        self.update_button_states()
    
    def display_level_info(self, level):
        """Display level info in the panel"""
        info = f"<b>ID:</b> {level['level_id']}<br>"
        info += f"<b>Name:</b> {level['level_name']}<br>"
        info += f"<b>Author:</b> {level['author']}<br>"
        info += f"<b>Song:</b> {level.get('song', 'N/A')}<br>"
        info += f"<b>Difficulty:</b> {level['difficulty']}<br>"
        info += f"<b>Length:</b> {level['length']}<br>"
        info += f"<b>Rated:</b> {'Yes' if level.get('is_rated') else 'No'}<br>"
        info += f"<b>Large:</b> {'Yes' if level.get('is_large') else 'No'}<br>"
        info += f"<b>Requester:</b> {level['requester']} ({level['platform']})<br>"
        info += f"<b>Attempts:</b> {level.get('attempts', 0)}"
        
        if level.get("is_fucked"):
            info += "<br><br><span style='color: red; font-weight: bold;'>⚠️ WARNING: Level is fucked - don't play on stream pls</span>"
            if level.get("fucked_note"):
                info += f"<br><b>Reason:</b> {level['fucked_note']}"
        
        self.level_info.setHtml(info)
    
    def update_button_states(self):
        """Enable/disable buttons based on selection"""
        has_selection = self.queue_list.currentItem() is not None
        
        self.copy_id_btn.setEnabled(has_selection)
        self.skip_btn.setEnabled(has_selection)
        self.mark_played_btn.setEnabled(has_selection)
        self.report_btn.setEnabled(has_selection)
        self.ban_requester_btn.setEnabled(has_selection)
        self.ban_creator_btn.setEnabled(has_selection)
        self.ban_id_btn.setEnabled(has_selection)
    
    def get_selected_level(self):
        """Get currently selected level"""
        current = self.queue_list.currentItem()
        if current:
            return current.data(Qt.ItemDataRole.UserRole)
        return None
    
    def copy_id(self):
        """Copy level ID to clipboard"""
        level = self.get_selected_level()
        if level:
            QApplication.clipboard().setText(str(level['level_id']))
            self.statusBar().showMessage(f"Copied ID: {level['level_id']}", 3000)
    
    def skip_level(self):
        """Skip current level"""
        level = self.get_selected_level()
        if level:
            self.queue_manager.remove_level(level['level_id'])
            self.statusBar().showMessage(f"Skipped: {level['level_name']}", 3000)
    
    def mark_played(self):
        """Mark level as played"""
        level = self.get_selected_level()
        if level:
            self.queue_manager.mark_as_played(level['level_id'])
            self.statusBar().showMessage(f"Marked as played: {level['level_name']}", 3000)
    
    def report_level(self):
        """Report level (will be implemented in phase 3)"""
        level = self.get_selected_level()
        if level:
            from report_dialog import ReportDialog
            dialog = ReportDialog(level, self.settings)
            dialog.exec()
    
    def ban_requester(self):
        """Ban requester"""
        level = self.get_selected_level()
        if level:
            confirm = QMessageBox.question(
                self,
                "Ban Requester",
                f"Ban {level['requester']} from requesting levels?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.queue_manager.ban_requester(level['requester'], level['platform'])
                self.statusBar().showMessage(f"Banned requester: {level['requester']}", 3000)
    
    def ban_creator(self):
        """Ban creator"""
        level = self.get_selected_level()
        if level:
            confirm = QMessageBox.question(
                self,
                "Ban Creator",
                f"Ban {level['author']} from being requested?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.queue_manager.ban_creator(level['author'])
                self.statusBar().showMessage(f"Banned creator: {level['author']}", 3000)
    
    def ban_id(self):
        """Ban level ID"""
        level = self.get_selected_level()
        if level:
            confirm = QMessageBox.question(
                self,
                "Ban Level ID",
                f"Ban level ID {level['level_id']} from being requested?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if confirm == QMessageBox.StandardButton.Yes:
                self.queue_manager.ban_level_id(level['level_id'])
                self.statusBar().showMessage(f"Banned level ID: {level['level_id']}", 3000)
    
    def open_settings(self):
        """Open settings window"""
        settings_window = SettingsWindow(self.settings, self)
        if settings_window.exec():
            # Settings were changed, reload services
            self.reload_services()
    
    def reload_services(self):
        """Reload services after settings change"""
        from main import log, save_settings
        
        # Save settings
        save_settings(self.settings)
        
        # Restart Twitch service
        if self.twitch_service:
            self.twitch_service.stop()
            self.twitch_service = None
        
        if self.settings.get("twitch_token") and self.settings.get("twitch_username"):
            self.twitch_service = TwitchService(self.settings)
            self.twitch_service.level_requested.connect(self.handle_level_request)
            self.twitch_service.delete_requested.connect(self.handle_delete_request)
            self.twitch_service.connection_changed.connect(self.update_connection_status)
            self.twitch_service.start()
            log("INFO", "Twitch service restarted")
        
        # Update automod
        self.automod_service.update_settings(self.settings)
        
        # Update OBS overlay
        if self.settings.get("obs_overlay_enabled"):
            if not self.obs_overlay:
                self.obs_overlay = OBSOverlay(self.settings)
                self.queue_manager.queue_changed.connect(self.update_obs_overlay)
            else:
                self.obs_overlay.update_settings(self.settings)
        elif self.obs_overlay:
            self.obs_overlay.close()
            self.obs_overlay = None
        
        # Update notification service
        self.notification_service.update_settings(self.settings)
        
        # Update backup timer
        if self.settings.get("backup_enabled", False):
            self.start_backup_timer()
        elif self.backup_timer:
            self.backup_timer.stop()
            self.backup_timer = None
        
        log("INFO", "Services reloaded")
    
    def open_donate(self):
        """Open donation page"""
        webbrowser.open("https://malikhw.github.io/donate")
    
    def handle_level_request(self, level_id, requester, platform):
        """Handle level request from chat"""
        from main import log
        
        # Check if accepting requests
        if not self.queue_manager.is_accepting():
            log("INFO", f"Rejected request from {requester} (not accepting)")
            return
        
        # Pass to queue manager (it will handle automod, filters, etc.)
        result = self.queue_manager.add_level(level_id, requester, platform)
        
        if result["success"]:
            self.notification_service.play_sound("new_level")
            log("INFO", f"Added level {level_id} from {requester} ({platform})")
        else:
            self.notification_service.play_sound("error")
            log("WARNING", f"Rejected level {level_id} from {requester}: {result.get('reason', 'Unknown')}")
    
    def handle_delete_request(self, requester, platform):
        """Handle delete request from chat"""
        from main import log
        
        success = self.queue_manager.delete_last_from_requester(requester, platform)
        
        if success:
            log("INFO", f"Deleted last level from {requester} ({platform})")
            self.statusBar().showMessage(f"Deleted last level from {requester}", 3000)
        else:
            log("INFO", f"No level to delete for {requester} ({platform})")
    
    def update_connection_status(self, service, connected):
        """Update connection status in status bar"""
        self.statusBar().showMessage(self.get_connection_status())
    
    def update_obs_overlay(self):
        """Update OBS overlay with current queue"""
        if self.obs_overlay:
            queue = self.queue_manager.get_queue()
            text = self.obs_overlay.format_text(queue)
            self.obs_overlay.update_text(text)
    
    def get_connection_status(self):
        """Get current connection status text"""
        statuses = []
        
        if self.twitch_service and self.twitch_service.is_connected():
            statuses.append("Twitch")
        
        if self.youtube_service and self.youtube_service.is_connected():
            statuses.append("YouTube")
        
        if statuses:
            return f"Connected: {', '.join(statuses)}"
        else:
            return "Disconnected"