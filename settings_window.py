import os
import webbrowser
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QWidget, QLabel, QLineEdit, QPushButton, QCheckBox,
                             QSpinBox, QComboBox, QFileDialog, QTextEdit, QGroupBox,
                             QMessageBox)
from PyQt6.QtCore import Qt

class SettingsWindow(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.init_ui()
    
    def init_ui(self):
        """Initialize the settings UI"""
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 700, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Add tabs
        self.tabs.addTab(self.create_connection_tab(), "Connection")
        self.tabs.addTab(self.create_commands_tab(), "Commands")
        self.tabs.addTab(self.create_automod_tab(), "Automod")
        self.tabs.addTab(self.create_filters_tab(), "Filters")
        self.tabs.addTab(self.create_obs_tab(), "OBS Overlay")
        self.tabs.addTab(self.create_sounds_tab(), "Sounds")
        self.tabs.addTab(self.create_backup_tab(), "Backup")
        self.tabs.addTab(self.create_advanced_tab(), "Advanced")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def create_connection_tab(self):
        """Create connection settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Twitch section
        twitch_group = QGroupBox("Twitch")
        twitch_layout = QVBoxLayout()
        
        # Token help
        token_help = QLabel("Get your token from <a href='https://twitchtokengenerator.com'>twitchtokengenerator.com</a><br>"
                           "Required scopes: chat:read, chat:edit, channel:moderate")
        token_help.setOpenExternalLinks(True)
        token_help.setWordWrap(True)
        twitch_layout.addWidget(token_help)
        
        # Token input
        token_label = QLabel("Twitch OAuth Token:")
        twitch_layout.addWidget(token_label)
        
        self.twitch_token_input = QLineEdit()
        self.twitch_token_input.setPlaceholderText("Put your Twitch token here")
        self.twitch_token_input.setText(self.settings.get("twitch_token", ""))
        self.twitch_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        twitch_layout.addWidget(self.twitch_token_input)
        
        # Username input
        username_label = QLabel("Twitch Username:")
        twitch_layout.addWidget(username_label)
        
        self.twitch_username_input = QLineEdit()
        self.twitch_username_input.setPlaceholderText("Your Twitch username")
        self.twitch_username_input.setText(self.settings.get("twitch_username", ""))
        twitch_layout.addWidget(self.twitch_username_input)
        
        twitch_group.setLayout(twitch_layout)
        layout.addWidget(twitch_group)
        
        # YouTube section
        youtube_group = QGroupBox("YouTube")
        youtube_layout = QVBoxLayout()
        
        self.youtube_enabled_cb = QCheckBox("I'm a YouTube streamer")
        self.youtube_enabled_cb.setChecked(self.settings.get("youtube_enabled", False))
        youtube_layout.addWidget(self.youtube_enabled_cb)
        
        youtube_help = QLabel("When enabled, you'll be asked for your livestream URL on app start")
        youtube_help.setWordWrap(True)
        youtube_layout.addWidget(youtube_help)
        
        youtube_group.setLayout(youtube_layout)
        layout.addWidget(youtube_group)
        
        # Streamer name
        streamer_label = QLabel("Streamer Name (for reports):")
        layout.addWidget(streamer_label)
        
        self.streamer_name_input = QLineEdit()
        self.streamer_name_input.setPlaceholderText("Your streamer name")
        self.streamer_name_input.setText(self.settings.get("streamer_name", ""))
        layout.addWidget(self.streamer_name_input)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_commands_tab(self):
        """Create commands settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Post command
        post_label = QLabel("Post Command:")
        layout.addWidget(post_label)
        
        self.post_command_input = QLineEdit()
        self.post_command_input.setText(self.settings.get("post_command", "!post"))
        layout.addWidget(self.post_command_input)
        
        # Delete command
        delete_label = QLabel("Delete Command:")
        layout.addWidget(delete_label)
        
        self.delete_command_input = QLineEdit()
        self.delete_command_input.setText(self.settings.get("delete_command", "!del"))
        layout.addWidget(self.delete_command_input)
        
        # Max IDs per user
        max_ids_label = QLabel("Max IDs per user per stream (0 = unlimited):")
        layout.addWidget(max_ids_label)
        
        self.max_ids_spin = QSpinBox()
        self.max_ids_spin.setMinimum(0)
        self.max_ids_spin.setMaximum(100)
        self.max_ids_spin.setValue(self.settings.get("max_ids_per_user", 0))
        layout.addWidget(self.max_ids_spin)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_automod_tab(self):
        """Create automod settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.per_user_cooldown_cb = QCheckBox("Per-user cooldown (60 seconds)")
        self.per_user_cooldown_cb.setChecked(self.settings.get("per_user_cooldown", True))
        layout.addWidget(self.per_user_cooldown_cb)
        
        self.block_same_level_cb = QCheckBox("Block same level when submitted by same user")
        self.block_same_level_cb.setChecked(self.settings.get("block_same_level_same_user", True))
        layout.addWidget(self.block_same_level_cb)
        
        self.reject_fucked_cb = QCheckBox("Reject crash/NSFW levels from database")
        self.reject_fucked_cb.setChecked(self.settings.get("reject_fucked_list", True))
        layout.addWidget(self.reject_fucked_cb)
        
        self.ignore_played_cb = QCheckBox("Ignore already-played levels")
        self.ignore_played_cb.setChecked(self.settings.get("ignore_played", True))
        layout.addWidget(self.ignore_played_cb)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_filters_tab(self):
        """Create filters settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Length filters
        length_group = QGroupBox("Length Filters")
        length_layout = QVBoxLayout()
        
        length_filters = self.settings.get("length_filters", {})
        
        self.length_tiny_cb = QCheckBox("Tiny")
        self.length_tiny_cb.setChecked(length_filters.get("tiny", True))
        length_layout.addWidget(self.length_tiny_cb)
        
        self.length_short_cb = QCheckBox("Short")
        self.length_short_cb.setChecked(length_filters.get("short", True))
        length_layout.addWidget(self.length_short_cb)
        
        self.length_medium_cb = QCheckBox("Medium")
        self.length_medium_cb.setChecked(length_filters.get("medium", True))
        length_layout.addWidget(self.length_medium_cb)
        
        self.length_long_cb = QCheckBox("Long")
        self.length_long_cb.setChecked(length_filters.get("long", True))
        length_layout.addWidget(self.length_long_cb)
        
        self.length_xl_cb = QCheckBox("XL")
        self.length_xl_cb.setChecked(length_filters.get("xl", True))
        length_layout.addWidget(self.length_xl_cb)
        
        length_group.setLayout(length_layout)
        layout.addWidget(length_group)
        
        # Difficulty filters
        diff_group = QGroupBox("Difficulty Filters")
        diff_layout = QVBoxLayout()
        
        difficulty_filters = self.settings.get("difficulty_filters", {})
        
        self.diff_auto_cb = QCheckBox("Auto")
        self.diff_auto_cb.setChecked(difficulty_filters.get("auto", True))
        diff_layout.addWidget(self.diff_auto_cb)
        
        self.diff_easy_cb = QCheckBox("Easy")
        self.diff_easy_cb.setChecked(difficulty_filters.get("easy", True))
        diff_layout.addWidget(self.diff_easy_cb)
        
        self.diff_normal_cb = QCheckBox("Normal")
        self.diff_normal_cb.setChecked(difficulty_filters.get("normal", True))
        diff_layout.addWidget(self.diff_normal_cb)
        
        self.diff_hard_cb = QCheckBox("Hard")
        self.diff_hard_cb.setChecked(difficulty_filters.get("hard", True))
        diff_layout.addWidget(self.diff_hard_cb)
        
        self.diff_harder_cb = QCheckBox("Harder")
        self.diff_harder_cb.setChecked(difficulty_filters.get("harder", True))
        diff_layout.addWidget(self.diff_harder_cb)
        
        self.diff_insane_cb = QCheckBox("Insane")
        self.diff_insane_cb.setChecked(difficulty_filters.get("insane", True))
        diff_layout.addWidget(self.diff_insane_cb)
        
        self.diff_demon_easy_cb = QCheckBox("Easy Demon")
        self.diff_demon_easy_cb.setChecked(difficulty_filters.get("demon-easy", True))
        diff_layout.addWidget(self.diff_demon_easy_cb)
        
        self.diff_demon_medium_cb = QCheckBox("Medium Demon")
        self.diff_demon_medium_cb.setChecked(difficulty_filters.get("demon-medium", True))
        diff_layout.addWidget(self.diff_demon_medium_cb)
        
        self.diff_demon_hard_cb = QCheckBox("Hard Demon")
        self.diff_demon_hard_cb.setChecked(difficulty_filters.get("demon-hard", True))
        diff_layout.addWidget(self.diff_demon_hard_cb)
        
        self.diff_demon_insane_cb = QCheckBox("Insane Demon")
        self.diff_demon_insane_cb.setChecked(difficulty_filters.get("demon-insane", True))
        diff_layout.addWidget(self.diff_demon_insane_cb)
        
        self.diff_demon_extreme_cb = QCheckBox("Extreme Demon")
        self.diff_demon_extreme_cb.setChecked(difficulty_filters.get("demon-extreme", True))
        diff_layout.addWidget(self.diff_demon_extreme_cb)
        
        diff_group.setLayout(diff_layout)
        layout.addWidget(diff_group)
        
        # Other filters
        other_group = QGroupBox("Other Filters")
        other_layout = QVBoxLayout()
        
        self.block_disliked_cb = QCheckBox("Block disliked levels")
        self.block_disliked_cb.setChecked(self.settings.get("block_disliked", False))
        other_layout.addWidget(self.block_disliked_cb)
        
        rated_label = QLabel("Rated Filter:")
        other_layout.addWidget(rated_label)
        
        self.rated_combo = QComboBox()
        self.rated_combo.addItems(["Any", "Rated Only", "Unrated Only"])
        self.rated_combo.setCurrentText(self.settings.get("rated_filter", "Any"))
        other_layout.addWidget(self.rated_combo)
        
        self.block_large_cb = QCheckBox("Block large levels (40k+ objects)")
        self.block_large_cb.setChecked(self.settings.get("block_large", False))
        other_layout.addWidget(self.block_large_cb)
        
        other_group.setLayout(other_layout)
        layout.addWidget(other_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_obs_tab(self):
        """Create OBS overlay settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.obs_enabled_cb = QCheckBox("Enable OBS Overlay")
        self.obs_enabled_cb.setChecked(self.settings.get("obs_overlay_enabled", False))
        layout.addWidget(self.obs_enabled_cb)
        
        self.obs_window_cb = QCheckBox("Show separate overlay window")
        self.obs_window_cb.setChecked(self.settings.get("obs_overlay_window_enabled", False))
        layout.addWidget(self.obs_window_cb)
        
        server_label = QLabel("HTML server always runs on port 6767 when overlay is enabled")
        server_label.setWordWrap(True)
        layout.addWidget(server_label)
        
        # Template
        template_label = QLabel("Template (variables: {level}, {author}, {id}, {next-level}, {next-author}):")
        layout.addWidget(template_label)
        
        self.obs_template_input = QTextEdit()
        self.obs_template_input.setMaximumHeight(100)
        self.obs_template_input.setText(self.settings.get("obs_overlay_template", "{level} by {author} (ID: {id})"))
        layout.addWidget(self.obs_template_input)
        
        # Font
        font_label = QLabel("Custom Font (.ttf):")
        layout.addWidget(font_label)
        
        font_layout = QHBoxLayout()
        self.obs_font_input = QLineEdit()
        self.obs_font_input.setText(self.settings.get("obs_overlay_font", ""))
        font_layout.addWidget(self.obs_font_input)
        
        font_btn = QPushButton("Browse")
        font_btn.clicked.connect(self.browse_font)
        font_layout.addWidget(font_btn)
        
        layout.addLayout(font_layout)
        
        # Size
        size_layout = QHBoxLayout()
        
        width_label = QLabel("Width:")
        size_layout.addWidget(width_label)
        
        self.obs_width_spin = QSpinBox()
        self.obs_width_spin.setMinimum(100)
        self.obs_width_spin.setMaximum(3840)
        self.obs_width_spin.setValue(self.settings.get("obs_overlay_width", 800))
        size_layout.addWidget(self.obs_width_spin)
        
        height_label = QLabel("Height:")
        size_layout.addWidget(height_label)
        
        self.obs_height_spin = QSpinBox()
        self.obs_height_spin.setMinimum(50)
        self.obs_height_spin.setMaximum(2160)
        self.obs_height_spin.setValue(self.settings.get("obs_overlay_height", 100))
        size_layout.addWidget(self.obs_height_spin)
        
        layout.addLayout(size_layout)
        
        # Transparency
        transparency_label = QLabel("Transparency (0-100%):")
        layout.addWidget(transparency_label)
        
        self.obs_transparency_spin = QSpinBox()
        self.obs_transparency_spin.setMinimum(0)
        self.obs_transparency_spin.setMaximum(100)
        self.obs_transparency_spin.setValue(self.settings.get("obs_overlay_transparency", 100))
        layout.addWidget(self.obs_transparency_spin)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_sounds_tab(self):
        """Create sounds settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.sounds_enabled_cb = QCheckBox("Enable Sounds")
        self.sounds_enabled_cb.setChecked(self.settings.get("sounds_enabled", False))
        layout.addWidget(self.sounds_enabled_cb)
        
        # New level sound
        new_level_label = QLabel("New Level Sound (.mp3/.ogg/.wav):")
        layout.addWidget(new_level_label)
        
        new_level_layout = QHBoxLayout()
        self.sound_new_level_input = QLineEdit()
        self.sound_new_level_input.setText(self.settings.get("sound_new_level", ""))
        new_level_layout.addWidget(self.sound_new_level_input)
        
        new_level_btn = QPushButton("Browse")
        new_level_btn.clicked.connect(lambda: self.browse_sound("new_level"))
        new_level_layout.addWidget(new_level_btn)
        
        layout.addLayout(new_level_layout)
        
        # Error sound
        error_label = QLabel("Error Sound (.mp3/.ogg/.wav):")
        layout.addWidget(error_label)
        
        error_layout = QHBoxLayout()
        self.sound_error_input = QLineEdit()
        self.sound_error_input.setText(self.settings.get("sound_error", ""))
        error_layout.addWidget(self.sound_error_input)
        
        error_btn = QPushButton("Browse")
        error_btn.clicked.connect(lambda: self.browse_sound("error"))
        error_layout.addWidget(error_btn)
        
        layout.addLayout(error_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_backup_tab(self):
        """Create backup settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.backup_enabled_cb = QCheckBox("Enable Automatic Backup")
        self.backup_enabled_cb.setChecked(self.settings.get("backup_enabled", False))
        layout.addWidget(self.backup_enabled_cb)
        
        # Interval
        interval_label = QLabel("Backup Interval (minutes):")
        layout.addWidget(interval_label)
        
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setMinimum(1)
        self.backup_interval_spin.setMaximum(120)
        self.backup_interval_spin.setValue(self.settings.get("backup_interval", 10))
        layout.addWidget(self.backup_interval_spin)
        
        # Manual controls
        manual_label = QLabel("Manual Backup:")
        layout.addWidget(manual_label)
        
        backup_now_btn = QPushButton("Backup Now")
        backup_now_btn.clicked.connect(self.backup_now)
        layout.addWidget(backup_now_btn)
        
        restore_btn = QPushButton("Restore from Backup")
        restore_btn.clicked.connect(self.restore_backup)
        layout.addWidget(restore_btn)
        
        open_folder_btn = QPushButton("Open Backup Folder")
        open_folder_btn.clicked.connect(self.open_backup_folder)
        layout.addWidget(open_folder_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.save_queue_cb = QCheckBox("Save queue on every change")
        self.save_queue_cb.setChecked(self.settings.get("save_queue_on_change", True))
        layout.addWidget(self.save_queue_cb)
        
        self.load_queue_cb = QCheckBox("Load queue on app start")
        self.load_queue_cb.setChecked(self.settings.get("load_queue_on_start", True))
        layout.addWidget(self.load_queue_cb)
        
        # Clear cache button
        clear_cache_btn = QPushButton("Clear Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        layout.addWidget(clear_cache_btn)
        
        # Reset played button
        reset_played_btn = QPushButton("Reset Played Levels")
        reset_played_btn.clicked.connect(self.reset_played)
        layout.addWidget(reset_played_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def browse_font(self):
        """Browse for font file"""
        filename, _ = QFileDialog.getOpenFileName(self, "Select Font", "", "TrueType Fonts (*.ttf)")
        if filename:
            self.obs_font_input.setText(filename)
    
    def browse_sound(self, sound_type):
        """Browse for sound file"""
        filename, _ = QFileDialog.getOpenFileName(self, "Select Sound", "", "Audio Files (*.mp3 *.ogg *.wav)")
        if filename:
            if sound_type == "new_level":
                self.sound_new_level_input.setText(filename)
            elif sound_type == "error":
                self.sound_error_input.setText(filename)
    
    def backup_now(self):
        """Create manual backup"""
        from backup_service import BackupService
        backup = BackupService()
        if backup.create_backup():
            QMessageBox.information(self, "Success", "Backup created successfully!")
        else:
            QMessageBox.warning(self, "Error", "Failed to create backup")
    
    def restore_backup(self):
        """Restore from backup"""
        filename, _ = QFileDialog.getOpenFileName(self, "Select Backup", "", "Backup Files (*.hgb-bkp)")
        if filename:
            from backup_service import BackupService
            backup = BackupService()
            if backup.restore_backup(filename):
                QMessageBox.information(self, "Success", "Backup restored successfully! Please restart the app.")
            else:
                QMessageBox.warning(self, "Error", "Failed to restore backup")
    
    def open_backup_folder(self):
        """Open backup folder"""
        from backup_service import BackupService
        backup = BackupService()
        backup.open_backup_folder()
    
    def clear_cache(self):
        """Clear GDBrowser cache"""
        from gd_integration import GDIntegration
        gd = GDIntegration()
        gd.clear_cache()
        QMessageBox.information(self, "Success", "Cache cleared!")
    
    def reset_played(self):
        """Reset played levels list"""
        confirm = QMessageBox.question(
            self,
            "Reset Played Levels",
            "Are you sure you want to reset the played levels list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            from queue_manager import QueueManager
            qm = QueueManager(self.settings)
            qm.reset_played()
            QMessageBox.information(self, "Success", "Played levels list reset!")
    
    def save_settings(self):
        """Save all settings"""
        # Connection
        self.settings["twitch_token"] = self.twitch_token_input.text().strip()
        self.settings["twitch_username"] = self.twitch_username_input.text().strip()
        self.settings["youtube_enabled"] = self.youtube_enabled_cb.isChecked()
        self.settings["streamer_name"] = self.streamer_name_input.text().strip()
        
        # Commands
        self.settings["post_command"] = self.post_command_input.text().strip()
        self.settings["delete_command"] = self.delete_command_input.text().strip()
        self.settings["max_ids_per_user"] = self.max_ids_spin.value()
        
        # Automod
        self.settings["per_user_cooldown"] = self.per_user_cooldown_cb.isChecked()
        self.settings["block_same_level_same_user"] = self.block_same_level_cb.isChecked()
        self.settings["reject_fucked_list"] = self.reject_fucked_cb.isChecked()
        self.settings["ignore_played"] = self.ignore_played_cb.isChecked()
        
        # Filters
        self.settings["length_filters"] = {
            "tiny": self.length_tiny_cb.isChecked(),
            "short": self.length_short_cb.isChecked(),
            "medium": self.length_medium_cb.isChecked(),
            "long": self.length_long_cb.isChecked(),
            "xl": self.length_xl_cb.isChecked()
        }
        
        self.settings["difficulty_filters"] = {
            "auto": self.diff_auto_cb.isChecked(),
            "easy": self.diff_easy_cb.isChecked(),
            "normal": self.diff_normal_cb.isChecked(),
            "hard": self.diff_hard_cb.isChecked(),
            "harder": self.diff_harder_cb.isChecked(),
            "insane": self.diff_insane_cb.isChecked(),
            "demon-easy": self.diff_demon_easy_cb.isChecked(),
            "demon-medium": self.diff_demon_medium_cb.isChecked(),
            "demon-hard": self.diff_demon_hard_cb.isChecked(),
            "demon-insane": self.diff_demon_insane_cb.isChecked(),
            "demon-extreme": self.diff_demon_extreme_cb.isChecked()
        }
        
        self.settings["block_disliked"] = self.block_disliked_cb.isChecked()
        self.settings["rated_filter"] = self.rated_combo.currentText()
        self.settings["block_large"] = self.block_large_cb.isChecked()
        
        # OBS
        self.settings["obs_overlay_enabled"] = self.obs_enabled_cb.isChecked()
        self.settings["obs_overlay_window_enabled"] = self.obs_window_cb.isChecked()
        self.settings["obs_overlay_template"] = self.obs_template_input.toPlainText()
        self.settings["obs_overlay_font"] = self.obs_font_input.text().strip()
        self.settings["obs_overlay_width"] = self.obs_width_spin.value()
        self.settings["obs_overlay_height"] = self.obs_height_spin.value()
        self.settings["obs_overlay_transparency"] = self.obs_transparency_spin.value()
        
        # Sounds
        self.settings["sounds_enabled"] = self.sounds_enabled_cb.isChecked()
        self.settings["sound_new_level"] = self.sound_new_level_input.text().strip()
        self.settings["sound_error"] = self.sound_error_input.text().strip()
        
        # Backup
        self.settings["backup_enabled"] = self.backup_enabled_cb.isChecked()
        self.settings["backup_interval"] = self.backup_interval_spin.value()
        
        # Advanced
        self.settings["save_queue_on_change"] = self.save_queue_cb.isChecked()
        self.settings["load_queue_on_start"] = self.load_queue_cb.isChecked()
        
        self.accept()