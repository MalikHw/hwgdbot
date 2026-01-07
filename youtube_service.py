import re
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import pytchat
    PYTCHAT_AVAILABLE = True
except ImportError:
    PYTCHAT_AVAILABLE = False

class YouTubeService(QThread):
    level_requested = pyqtSignal(str, str, str)  # level_id, requester, platform
    delete_requested = pyqtSignal(str, str)  # requester, platform
    connection_status = pyqtSignal(str)
    
    def __init__(self, livestream_url: str, post_cmd: str = '!post', del_cmd: str = '!del'):
        super().__init__()
        self.livestream_url = livestream_url
        self.post_cmd = post_cmd
        self.del_cmd = del_cmd
        self.running = False
        self.chat = None
    
    def run(self):
        if not PYTCHAT_AVAILABLE:
            self.connection_status.emit("❌ pytchat not installed")
            return
        
        self.running = True
        self.connection_status.emit("Connecting to YouTube...")
        
        try:
            # Extract video ID from URL
            video_id = self.extract_video_id(self.livestream_url)
            
            if not video_id:
                self.connection_status.emit("❌ Invalid YouTube URL")
                return
            
            self.chat = pytchat.create(video_id=video_id)
            self.connection_status.emit(f"✅ Connected to YouTube Live")
            
            while self.running and self.chat.is_alive():
                for message in self.chat.get().sync_items():
                    if not self.running:
                        break
                    
                    self.parse_message(message.author.name, message.message)
        
        except Exception as e:
            self.connection_status.emit(f"❌ YouTube error: {e}")
        
        finally:
            if self.chat:
                self.chat.terminate()
            self.connection_status.emit("Disconnected from YouTube")
    
    def extract_video_id(self, url: str) -> str:
        # Extract video ID from various YouTube URL formats
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/live/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def parse_message(self, username: str, message: str):
        # Check for post command (configurable)
        post_pattern = re.escape(self.post_cmd) + r'\s+(\d+)'
        post_match = re.match(post_pattern, message, re.IGNORECASE)
        
        if post_match:
            level_id = post_match.group(1)
            self.level_requested.emit(level_id, username, 'youtube')
            return
        
        # Check for delete command (configurable)
        del_pattern = re.escape(self.del_cmd)
        if re.match(del_pattern, message, re.IGNORECASE):
            self.delete_requested.emit(username, 'youtube')
    
    def stop(self):
        self.running = False
        if self.chat:
            self.chat.terminate()
        self.wait()
