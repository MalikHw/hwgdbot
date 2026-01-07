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
        
        # Commands tab
        tabs.addTab(self.create_commands_tab(), "Commands")
        
        # Automod tab
        tabs.addTab(self.create_automod_tab(), "Automod")
        
        # Filters tab
        tabs.addTab(self.create_filters_tab(), "Filters")
        
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
        donate_btn.clicked.connect(lambda: self.parent().open_donate_page() if hasattr(self.parent(), 'open_donate_page') else webbrowser.open("https://malikhw.github.io/donate"))
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
        
        help_label = QLabel("<b>How to get your Twitch OAuth token:</b><br>"
                           "1. Visit: <a href='https://twitchtokengenerator.com'>twitchtokengenerator.com</a><br>"
                           "2. Click 'Generate Token'<br>"
                           "3. Select scopes: <b>chat:read</b>, <b>chat:edit</b>, <b>channel:moderate</b><br>"
                           "4. Authorize and copy the token<br>"
                           "5. Paste below (nothing is sent to me, stored locally only!)")
        help_label.setOpenExternalLinks(True)
        help_label.setWordWrap(True)
        help_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
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
        
        self.youtube_enable = QCheckBox("I'm a YouTube streamer")
        self.youtube_enable.setToolTip("Every time you start the app, you'll be asked for your livestream URL")
        youtube_layout.addWidget(self.youtube_enable)
        
        yt_note = QLabel("Note: When enabled, the app will ask for your YouTube livestream URL on every startup. "
                        "If the URL is invalid, YouTube chat connection will be skipped.")
        yt_note.setWordWrap(True)
        yt_note.setStyleSheet("QLabel { color: #666; font-size: 11px; }")
        youtube_layout.addWidget(yt_note)
        
        youtube_group.setLayout(youtube_layout)
        layout.addWidget(youtube_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_commands_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<b>Chat Commands Configuration</b>"))
        layout.addWidget(QLabel("Customize the commands users type in chat:"))
        
        # Post command
        post_layout = QHBoxLayout()
        post_layout.addWidget(QLabel("Submit Level Command:"))
        self.post_command = QLineEdit()
        self.post_command.setPlaceholderText("!post")
        self.post_command.setToolTip("Command for submitting levels (e.g., !post 12345)")
        post_layout.addWidget(self.post_command)
        layout.addLayout(post_layout)
        
        # Delete command
        del_layout = QHBoxLayout()
        del_layout.addWidget(QLabel("Delete Level Command:"))
        self.del_command = QLineEdit()
        self.del_command.setPlaceholderText("!del")
        self.del_command.setToolTip("Command for deleting your last submitted level")
        del_layout.addWidget(self.del_command)
        layout.addLayout(del_layout)
        
        note = QLabel("Note: Users can delete their most recent submission using the delete command.\n"
                     "Example: User types '!post 123' then '!del' to remove it.")
        note.setWordWrap(True)
        note.setStyleSheet("QLabel { color: #666; font-size: 11px; padding: 10px; }")
        layout.addWidget(note)
        
        layout.addWidget(QLabel("---"))
        
        # Max IDs per user
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max levels per user per stream:"))
        self.max_ids_spinner = QSpinBox()
        self.max_ids_spinner.setRange(0, 100)
        self.max_ids_spinner.setValue(0)
        self.max_ids_spinner.setSpecialValueText("Unlimited")
        self.max_ids_spinner.setToolTip("0 = unlimited, 1 = one level per user, etc.\nResets when queue is cleared or app restarts")
        max_layout.addWidget(self.max_ids_spinner)
        max_layout.addStretch()
        layout.addLayout(max_layout)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_filters_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<b>Level Filters</b>"))
        layout.addWidget(QLabel("Only accept levels matching these criteria:"))
        
        # Length filter
        length_group = QGroupBox("Length")
        length_layout = QVBoxLayout()
        
        self.filter_lengths = {}
        for length in ['tiny', 'short', 'medium', 'long', 'xl']:
            cb = QCheckBox(length.capitalize())
            cb.setChecked(True)
            self.filter_lengths[length] = cb
            length_layout.addWidget(cb)
        
        length_group.setLayout(length_layout)
        layout.addWidget(length_group)
        
        # Difficulty filter
        diff_group = QGroupBox("Difficulty")
        diff_layout = QVBoxLayout()
        
        self.filter_difficulties = {}
        difficulties = ['auto', 'easy', 'normal', 'hard', 'harder', 'insane', 
                       'demon-easy', 'demon-medium', 'demon-hard', 'demon-insane', 'demon-extreme']
        
        for diff in difficulties:
            cb = QCheckBox(diff.replace('-', ' ').title())
            cb.setChecked(True)
            self.filter_difficulties[diff] = cb
            diff_layout.addWidget(cb)
        
        diff_group.setLayout(diff_layout)
        layout.addWidget(diff_group)
        
        # Other filters
        other_group = QGroupBox("Other Filters")
        other_layout = QVBoxLayout()
        
        self.filter_disliked = QCheckBox("Block disliked levels")
        other_layout.addWidget(self.filter_disliked)
        
        rated_layout = QHBoxLayout()
        rated_layout.addWidget(QLabel("Rated Status:"))
        self.rated_filter = QComboBox()
        self.rated_filter.addItems(["Any", "Rated Only", "Unrated Only"])
        rated_layout.addWidget(self.rated_filter)
        rated_layout.addStretch()
        other_layout.addLayout(rated_layout)
        
        self.filter_large = QCheckBox("Block large levels (40k+ objects)")
        other_layout.addWidget(self.filter_large)
        
        other_group.setLayout(other_layout)
        layout.addWidget(other_group)
        
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
        
        # Commands
        self.post_command.setText(self.settings.get('post_command', '!post'))
        self.del_command.setText(self.settings.get('del_command', '!del'))
        self.max_ids_spinner.setValue(self.settings.get('max_ids_per_user', 0))
        
        # Filters
        filters = self.settings.get('level_filters', {})
        
        allowed_lengths = filters.get('lengths', ['tiny', 'short', 'medium', 'long', 'xl'])
        for length, cb in self.filter_lengths.items():
            cb.setChecked(length in allowed_lengths)
        
        allowed_diffs = filters.get('difficulties', ['auto', 'easy', 'normal', 'hard', 'harder', 'insane', 
                                                     'demon-easy', 'demon-medium', 'demon-hard', 'demon-insane', 'demon-extreme'])
        for diff, cb in self.filter_difficulties.items():
            cb.setChecked(diff in allowed_diffs)
        
        self.filter_disliked.setChecked(filters.get('filter_disliked', False))
        self.filter_large.setChecked(filters.get('filter_large', False))
        
        rated_filter = filters.get('rated_filter', 'any')
        if rated_filter == 'rated_only':
            self.rated_filter.setCurrentIndex(1)
        elif rated_filter == 'unrated_only':
            self.rated_filter.setCurrentIndex(2)
        else:
            self.rated_filter.setCurrentIndex(0)
        
        # Automod
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
        
        # Commands
        self.settings['post_command'] = self.post_command.text().strip() or '!post'
        self.settings['del_command'] = self.del_command.text().strip() or '!del'
        self.settings['max_ids_per_user'] = self.max_ids_spinner.value()
        
        # Filters
        allowed_lengths = [length for length, cb in self.filter_lengths.items() if cb.isChecked()]
        allowed_diffs = [diff for diff, cb in self.filter_difficulties.items() if cb.isChecked()]
        
        rated_idx = self.rated_filter.currentIndex()
        rated_filter = 'any'
        if rated_idx == 1:
            rated_filter = 'rated_only'
        elif rated_idx == 2:
            rated_filter = 'unrated_only'
        
        self.settings['level_filters'] = {
            'lengths': allowed_lengths,
            'difficulties': allowed_diffs,
            'filter_disliked': self.filter_disliked.isChecked(),
            'filter_large': self.filter_large.isChecked(),
            'rated_filter': rated_filter
        }
        
        # Automod
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
