import socket
import re
from PyQt6.QtCore import QThread, pyqtSignal

class TwitchService(QThread):
    level_requested = pyqtSignal(str, str, str)  # level_id, requester, platform
    delete_requested = pyqtSignal(str, str)  # requester, platform
    connection_changed = pyqtSignal(str, bool)  # service, connected
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.running = False
        self.connected = False
        self.sock = None
        
        self.server = "irc.chat.twitch.tv"
        self.port = 6667
        self.token = settings.get("twitch_token", "")
        self.channel = settings.get("twitch_username", "").lower()
        self.nickname = self.channel
        
        self.post_command = settings.get("post_command", "!post")
        self.delete_command = settings.get("delete_command", "!del")
    
    def run(self):
        """Main thread loop"""
        from main import log
        
        self.running = True
        
        try:
            # Connect to Twitch IRC
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server, self.port))
            
            # Authenticate
            self.sock.send(f"PASS oauth:{self.token}\r\n".encode("utf-8"))
            self.sock.send(f"NICK {self.nickname}\r\n".encode("utf-8"))
            self.sock.send(f"JOIN #{self.channel}\r\n".encode("utf-8"))
            
            self.connected = True
            self.connection_changed.emit("twitch", True)
            log("INFO", f"Connected to Twitch channel #{self.channel}")
            
            # Main message loop
            buffer = ""
            while self.running:
                try:
                    data = self.sock.recv(2048).decode("utf-8", errors="ignore")
                    if not data:
                        break
                    
                    buffer += data
                    lines = buffer.split("\r\n")
                    buffer = lines.pop()
                    
                    for line in lines:
                        self.handle_message(line)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    log("ERROR", f"Twitch receive error: {e}")
                    break
        
        except Exception as e:
            log("ERROR", f"Twitch connection error: {e}")
        
        finally:
            self.connected = False
            self.connection_changed.emit("twitch", False)
            if self.sock:
                self.sock.close()
            log("INFO", "Disconnected from Twitch")
    
    def handle_message(self, line):
        """Handle IRC message"""
        from main import log
        
        # Respond to PING
        if line.startswith("PING"):
            self.sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            return
        
        # Parse PRIVMSG
        match = re.match(r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)", line)
        if match:
            username = match.group(1)
            message = match.group(2).strip()
            
            # Check for post command
            if message.startswith(self.post_command):
                parts = message.split()
                if len(parts) >= 2:
                    level_id = parts[1]
                    # Extract numeric ID
                    level_id = re.sub(r'\D', '', level_id)
                    if level_id:
                        log("INFO", f"Twitch: {username} requested level {level_id}")
                        self.level_requested.emit(level_id, username, "twitch")
            
            # Check for delete command
            elif message.startswith(self.delete_command):
                log("INFO", f"Twitch: {username} requested delete")
                self.delete_requested.emit(username, "twitch")
    
    def send_message(self, message):
        """Send message to channel"""
        if self.connected and self.sock:
            try:
                self.sock.send(f"PRIVMSG #{self.channel} :{message}\r\n".encode("utf-8"))
            except Exception as e:
                from main import log
                log("ERROR", f"Failed to send Twitch message: {e}")
    
    def ban_user(self, username):
        """Ban user from channel"""
        self.send_message(f"/ban {username}")
        from main import log
        log("INFO", f"Banned {username} from Twitch channel")
    
    def is_connected(self):
        """Check if connected"""
        return self.connected
    
    def stop(self):
        """Stop the service"""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.wait()