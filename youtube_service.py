import re
from PyQt6.QtCore import QThread, pyqtSignal

class YouTubeService(QThread):
    level_requested = pyqtSignal(str, str, str)  # level_id, requester, platform
    delete_requested = pyqtSignal(str, str)  # requester, platform
    connection_changed = pyqtSignal(str, bool)  # service, connected
    
    def __init__(self, settings, livestream_url):
        super().__init__()
        self.settings = settings
        self.livestream_url = livestream_url
        self.running = False
        self.connected = False
        self.chat = None
        
        self.post_command = settings.get("post_command", "!post")
        self.delete_command = settings.get("delete_command", "!del")
    
    def run(self):
        """Main thread loop"""
        from main import log
        
        try:
            import pytchat
            
            self.running = True
            
            # Extract video ID from URL
            video_id = self.extract_video_id(self.livestream_url)
            if not video_id:
                log("ERROR", "Invalid YouTube URL")
                return
            
            # Connect to YouTube chat
            self.chat = pytchat.create(video_id=video_id)
            self.connected = True
            self.connection_changed.emit("youtube", True)
            log("INFO", f"Connected to YouTube livestream {video_id}")
            
            # Main message loop
            while self.running and self.chat.is_alive():
                try:
                    for c in self.chat.get().sync_items():
                        if not self.running:
                            break
                        
                        self.handle_message(c.author.name, c.message)
                
                except Exception as e:
                    log("ERROR", f"YouTube chat error: {e}")
                    break
        
        except ImportError:
            log("ERROR", "pytchat not installed")
        except Exception as e:
            log("ERROR", f"YouTube connection error: {e}")
        
        finally:
            self.connected = False
            self.connection_changed.emit("youtube", False)
            if self.chat:
                self.chat.terminate()
            log("INFO", "Disconnected from YouTube")
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/live/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def handle_message(self, username, message):
        """Handle chat message"""
        from main import log
        
        message = message.strip()
        
        # Check for post command
        if message.startswith(self.post_command):
            parts = message.split()
            if len(parts) >= 2:
                level_id = parts[1]
                # Extract numeric ID
                level_id = re.sub(r'\D', '', level_id)
                if level_id:
                    log("INFO", f"YouTube: {username} requested level {level_id}")
                    self.level_requested.emit(level_id, username, "youtube")
        
        # Check for delete command
        elif message.startswith(self.delete_command):
            log("INFO", f"YouTube: {username} requested delete")
            self.delete_requested.emit(username, "youtube")
    
    def is_connected(self):
        """Check if connected"""
        return self.connected
    
    def stop(self):
        """Stop the service"""
        self.running = False
        if self.chat:
            try:
                self.chat.terminate()
            except:
                pass
        self.wait()