import os
import platform
from datetime import datetime, timedelta
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

class NotificationService:
    def __init__(self, settings):
        self.settings = settings
        self.last_sound_time = {}
        self.players = {}
    
    def update_settings(self, settings):
        """Update settings"""
        self.settings = settings
    
    def play_sound(self, sound_type):
        """Play sound if enabled and not spamming"""
        if not self.settings.get("sounds_enabled", False):
            return
        
        # Check spam prevention (max once every 2 seconds)
        now = datetime.now()
        if sound_type in self.last_sound_time:
            elapsed = (now - self.last_sound_time[sound_type]).total_seconds()
            if elapsed < 2:
                return
        
        # Get sound file path
        if sound_type == "new_level":
            sound_path = self.settings.get("sound_new_level", "")
        elif sound_type == "error":
            sound_path = self.settings.get("sound_error", "")
        else:
            return
        
        if not sound_path or not os.path.exists(sound_path):
            return
        
        try:
            # Create player if needed
            if sound_type not in self.players:
                self.players[sound_type] = QMediaPlayer()
                audio_output = QAudioOutput()
                self.players[sound_type].setAudioOutput(audio_output)
            
            # Play sound
            player = self.players[sound_type]
            player.setSource(QUrl.fromLocalFile(sound_path))
            player.play()
            
            # Update last play time
            self.last_sound_time[sound_type] = now
            
        except Exception as e:
            from main import log
            log("ERROR", f"Failed to play sound {sound_type}: {e}")
    
    def show_notification(self, title, message):
        """Show system notification"""
        try:
            if platform.system() == "Windows":
                try:
                    from windows_toasts import Toast, WindowsToaster
                    toaster = WindowsToaster("HwGDBot")
                    toast = Toast()
                    toast.text_fields = [title, message]
                    toaster.show_toast(toast)
                except ImportError:
                    pass  # windows-toasts not available
        except Exception as e:
            from main import log
            log("ERROR", f"Failed to show notification: {e}")