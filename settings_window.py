from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QCheckBox, QTabWidget, QWidget, QFileDialog,
                             QMessageBox, QSpinBox, QComboBox, QGroupBox, QTextEdit)
from PyQt6.QtCore import Qt
from pathlib import Path
import json
import webbrowser
import zipfile
import os
from datetime import datetime

class SettingsWindow(QDialog):
    def __init__(self, settings: dict, data_dir: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HwGDBot Settings")
        self.resize(700, 600)
        self.settings = settings.copy()
        self.data_dir = data_dir
        
        self.setup_ui()
        self.load_values()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        tabs = QTabWidget()
        
        # Connection tab
        tabs.addTab(self.create_connection_tab(), "Connection")
        
        # Automod tab
        tabs.addTab(self.create_automod_tab(), "Automod")
        
        # OBS Overlay tab
        tabs.addTab(self.create_obs_tab(), "OBS Overlay")
        
        # Sounds tab
        tabs.addTab(self.create_sounds_tab(), "Sounds")
        
        # Backup tab
        tabs.addTab(self.create_backup_tab(), "Backup")
        
        # Advanced tab
        tabs.addTab(self.create_advanced_tab(), "Advanced")
        
        layout.addWidget(tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        donate_btn = QPushButton("💝 Donate")
        donate_btn.clicked.connect(lambda: webbrowser.open("https://malikhw.github.io/donate"))
        donate_btn.setStyleSheet("QPushButton { background-color: #ff4444; color: white; font-weight: bold; }")
        button_layout.addWidget(donate_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_connection_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Twitch settings
        twitch_group = QGroupBox("Twitch Connection")
        twitch_layout = QVBoxLayout()
        
        help_label = QLabel("Get your token from: <a href='https://twitchtokengenerator.com'>twitchtokengenerator.com</a>")
        help_label.setOpenExternalLinks(True)
        help_label.setWordWrap(True)
        twitch_layout.addWidget(help_label)
        
        twitch_layout.addWidget(QLabel("Twitch OAuth Token (nothing will be sent to me):"))
        self.twitch_token_input = QLineEdit()
        self.twitch_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        twitch_layout.addWidget(self.twitch_token_input)
        
        twitch_layout.addWidget(QLabel("Twitch Channel (your username):"))
        self.twitch_channel_input = QLineEdit()
        twitch_layout.addWidget(self.twitch_channel_input)
        
        twitch_group.setLayout(twitch_layout)
        layout.addWidget(twitch_group)
        
        # YouTube settings
        youtube_group = QGroupBox("YouTube Connection")
        youtube_layout = QVBoxLayout()
        
        self.youtube_enable = QCheckBox("Enable YouTube Chat Monitoring")
        self.youtube_enable.setToolTip("You'll be asked for livestream URL on every app start")
        youtube_layout.addWidget(self.youtube_enable)
        
        youtube_group.setLayout(youtube_layout)
        layout.addWidget(youtube_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_automod_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Automod Features:"))
        
        self.automod_cooldown = QCheckBox("Enable per-user cooldown (60s)")
        layout.addWidget(self.automod_cooldown)
        
        self.automod_spam = QCheckBox("Block same level 3x from same user")
        layout.addWidget(self.automod_spam)
        
        self.automod_fucked = QCheckBox("Reject crash/NSFW levels from database")
        layout.addWidget(self.automod_fucked)
        
        self.automod_played = QCheckBox("Ignore already played levels per session")
        layout.addWidget(self.automod_played)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_obs_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.obs_enable = QCheckBox("Enable OBS Overlay")
        layout.addWidget(self.obs_enable)
        
        layout.addWidget(QLabel("Overlay Text Template:"))
        layout.addWidget(QLabel("Variables: {level}, {author}, {id}, {next-level}, {next-author}"))
        self.obs_template = QTextEdit()
        self.obs_template.setMaximumHeight(100)
        layout.addWidget(self.obs_template)
        
        # Font selection
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font File (.ttf):"))
        self.obs_font_path = QLineEdit()
        font_btn = QPushButton("Browse...")
        font_btn.clicked.connect(self.browse_font)
        font_layout.addWidget(self.obs_font_path)
        font_layout.addWidget(font_btn)
        layout.addLayout(font_layout)
        
        # Size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Window Size:"))
        self.obs_width = QSpinBox()
        self.obs_width.setRange(200, 2000)
        self.obs_width.setValue(600)
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.obs_width)
        self.obs_height = QSpinBox()
        self.obs_height.setRange(100, 1000)
        self.obs_height.setValue(100)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(self.obs_height)
        layout.addLayout(size_layout)
        
        # Transparency
        trans_layout = QHBoxLayout()
        trans_layout.addWidget(QLabel("Background Transparency:"))
        self.obs_transparency = QSpinBox()
        self.obs_transparency.setRange(0, 100)
        self.obs_transparency.setValue(0)
        self.obs_transparency.setSuffix("%")
        trans_layout.addWidget(self.obs_transparency)
        layout.addLayout(trans_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_sounds_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.sounds_enable = QCheckBox("Enable Sound Notifications")
        layout.addWidget(self.sounds_enable)
        
        # New level sound
        new_layout = QHBoxLayout()
        new_layout.addWidget(QLabel("New Level Added Sound:"))
        self.sound_new_path = QLineEdit()
        new_btn = QPushButton("Browse...")
        new_btn.clicked.connect(lambda: self.browse_sound('new'))
        new_layout.addWidget(self.sound_new_path)
        new_layout.addWidget(new_btn)
        layout.addLayout(new_layout)
        
        # Error sound
        error_layout = QHBoxLayout()
        error_layout.addWidget(QLabel("Error/Blocked Sound:"))
        self.sound_error_path = QLineEdit()
        error_btn = QPushButton("Browse...")
        error_btn.clicked.connect(lambda: self.browse_sound('error'))
        error_layout.addWidget(self.sound_error_path)
        error_layout.addWidget(error_btn)
        layout.addLayout(error_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_backup_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Local Automatic Backup"))
        layout.addWidget(QLabel("Backups are saved to: Documents/HwGDBot/"))
        
        self.backup_enable = QCheckBox("Enable Automatic Backup")
        layout.addWidget(self.backup_enable)
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Backup Interval:"))
        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 120)
        self.backup_interval.setValue(10)
        self.backup_interval.setSuffix(" minutes")
        interval_layout.addWidget(self.backup_interval)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        backup_btn = QPushButton("Backup Now")
        backup_btn.clicked.connect(self.backup_now)
        layout.addWidget(backup_btn)
        
        restore_btn = QPushButton("Restore from Backup...")
        restore_btn.clicked.connect(self.restore_backup)
        layout.addWidget(restore_btn)
        
        open_folder_btn = QPushButton("Open Backup Folder")
        open_folder_btn.clicked.connect(self.open_backup_folder)
        layout.addWidget(open_folder_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.save_queue = QCheckBox("Save queue on every change")
        layout.addWidget(self.save_queue)
        
        self.load_queue = QCheckBox("Load queue on app start")
        layout.addWidget(self.load_queue)
        
        clear_cache_btn = QPushButton("Clear Level Cache")
        clear_cache_btn.clicked.connect(self.clear_cache)
        layout.addWidget(clear_cache_btn)
        
        reset_played_btn = QPushButton("Reset Played Levels")
        reset_played_btn.clicked.connect(self.reset_played)
        layout.addWidget(reset_played_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def browse_font(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Font File", "", "Font Files (*.ttf)")
        if path:
            self.obs_font_path.setText(path)
    
    def browse_sound(self, sound_type: str):
        path, _ = QFileDialog.getOpenFileName(self, "Select Sound File", "", 
                                              "Audio Files (*.mp3 *.ogg *.wav)")
        if path:
            if sound_type == 'new':
                self.sound_new_path.setText(path)
            else:
                self.sound_error_path.setText(path)
    
    def clear_cache(self):
        cache_file = self.data_dir / "cache.json"
        if cache_file.exists():
            cache_file.unlink()
        QMessageBox.information(self, "Success", "Level cache cleared!")
    
    def reset_played(self):
        played_file = self.data_dir / "played.json"
        if played_file.exists():
            played_file.unlink()
        QMessageBox.information(self, "Success", "Played levels list reset!")
    
    def backup_now(self):
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
            
            QMessageBox.information(self, "Success", 
                                   f"Backup saved to:\n{backup_file}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backup failed: {e}")
    
    def restore_backup(self):
        try:
            # Get Documents folder
            if os.name == 'nt':  # Windows
                docs_path = Path(os.path.expanduser('~')) / 'Documents'
            else:  # Linux/macOS
                docs_path = Path(os.path.expanduser('~')) / 'Documents'
            
            backup_dir = docs_path / 'HwGDBot'
            
            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select Backup File",
                str(backup_dir),
                "Backup Files (*.hgb-bkp)"
            )
            
            if not file_path:
                return
            
            # Extract zip file
            with zipfile.ZipFile(file_path, 'r') as zipf:
                zipf.extractall(self.data_dir)
            
            QMessageBox.information(self, "Success", 
                                   "Backup restored! Please restart the app.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Restore failed: {e}")
    
    def open_backup_folder(self):
        try:
            if os.name == 'nt':  # Windows
                docs_path = Path(os.path.expanduser('~')) / 'Documents'
            else:  # Linux/macOS
                docs_path = Path(os.path.expanduser('~')) / 'Documents'
            
            backup_dir = docs_path / 'HwGDBot'
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Open folder in file manager
            if os.name == 'nt':  # Windows
                os.startfile(backup_dir)
            elif os.uname().sysname == 'Darwin':  # macOS
                os.system(f'open "{backup_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{backup_dir}"')
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder: {e}")
    
    def load_values(self):
        self.twitch_token_input.setText(self.settings.get('twitch_token', ''))
        self.twitch_channel_input.setText(self.settings.get('twitch_channel', ''))
        self.youtube_enable.setChecked(self.settings.get('enable_youtube', False))
        
        self.automod_cooldown.setChecked(self.settings.get('automod_cooldown', True))
        self.automod_spam.setChecked(self.settings.get('automod_spam', True))
        self.automod_fucked.setChecked(self.settings.get('automod_fucked', True))
        self.automod_played.setChecked(self.settings.get('automod_played', True))
        
        self.obs_enable.setChecked(self.settings.get('enable_obs_overlay', False))
        self.obs_template.setText(self.settings.get('obs_template', 'Next: {next-level} by {next-author}'))
        self.obs_font_path.setText(self.settings.get('obs_font_path', ''))
        self.obs_width.setValue(self.settings.get('obs_width', 600))
        self.obs_height.setValue(self.settings.get('obs_height', 100))
        self.obs_transparency.setValue(self.settings.get('obs_transparency', 0))
        
        self.sounds_enable.setChecked(self.settings.get('sounds_enable', False))
        self.sound_new_path.setText(self.settings.get('sound_new_path', ''))
        self.sound_error_path.setText(self.settings.get('sound_error_path', ''))
        
        self.backup_enable.setChecked(self.settings.get('backup_enable', False))
        self.backup_interval.setValue(self.settings.get('backup_interval', 10))
        
        self.save_queue.setChecked(self.settings.get('save_queue_on_change', True))
        self.load_queue.setChecked(self.settings.get('load_queue_on_start', True))
    
    def save_settings(self):
        self.settings['twitch_token'] = self.twitch_token_input.text().strip()
        self.settings['twitch_channel'] = self.twitch_channel_input.text().strip()
        self.settings['enable_youtube'] = self.youtube_enable.isChecked()
        
        self.settings['automod_cooldown'] = self.automod_cooldown.isChecked()
        self.settings['automod_spam'] = self.automod_spam.isChecked()
        self.settings['automod_fucked'] = self.automod_fucked.isChecked()
        self.settings['automod_played'] = self.automod_played.isChecked()
        
        self.settings['enable_obs_overlay'] = self.obs_enable.isChecked()
        self.settings['obs_template'] = self.obs_template.toPlainText()
        self.settings['obs_font_path'] = self.obs_font_path.text()
        self.settings['obs_width'] = self.obs_width.value()
        self.settings['obs_height'] = self.obs_height.value()
        self.settings['obs_transparency'] = self.obs_transparency.value()
        
        self.settings['sounds_enable'] = self.sounds_enable.isChecked()
        self.settings['sound_new_path'] = self.sound_new_path.text()
        self.settings['sound_error_path'] = self.sound_error_path.text()
        
        self.settings['backup_enable'] = self.backup_enable.isChecked()
        self.settings['backup_interval'] = self.backup_interval.value()
        
        self.settings['save_queue_on_change'] = self.save_queue.isChecked()
        self.settings['load_queue_on_start'] = self.load_queue.isChecked()
        
        # Save to file
        settings_file = self.data_dir / "settings.json"
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2)
        
        self.accept()
    
    def get_settings(self):
        return self.settings
