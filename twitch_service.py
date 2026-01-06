import socket
import re
from PyQt6.QtCore import QThread, pyqtSignal

class TwitchService(QThread):
    level_requested = pyqtSignal(str, str, str)  # level_id, requester, platform
    connection_status = pyqtSignal(str)
    
    def __init__(self, token: str, channel: str):
        super().__init__()
        self.token = token
        self.channel = channel.lower().strip('#')
        self.running = False
        self.sock = None
    
    def run(self):
        self.running = True
        self.connection_status.emit("Connecting to Twitch...")
        
        try:
            self.sock = socket.socket()
            self.sock.connect(('irc.chat.twitch.tv', 6667))
            
            self.sock.send(f"PASS oauth:{self.token}\n".encode('utf-8'))
            self.sock.send(f"NICK {self.channel}\n".encode('utf-8'))
            self.sock.send(f"JOIN #{self.channel}\n".encode('utf-8'))
            
            self.connection_status.emit(f"✅ Connected to Twitch (#{self.channel})")
            
            buffer = ""
            
            while self.running:
                try:
                    data = self.sock.recv(2048).decode('utf-8', errors='ignore')
                    buffer += data
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line.startswith('PING'):
                            self.sock.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
                            continue
                        
                        self.parse_message(line)
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Twitch recv error: {e}")
                    break
        
        except Exception as e:
            self.connection_status.emit(f"❌ Twitch connection failed: {e}")
        
        finally:
            if self.sock:
                self.sock.close()
            self.connection_status.emit("Disconnected from Twitch")
    
    def parse_message(self, line: str):
        # Parse IRC message format
        match = re.match(r':(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)', line)
        
        if not match:
            return
        
        username = match.group(1)
        message = match.group(2).strip()
        
        # Check for !post command
        post_match = re.match(r'!post\s+(\d+)', message, re.IGNORECASE)
        
        if post_match:
            level_id = post_match.group(1)
            self.level_requested.emit(level_id, username, 'twitch')
    
    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.wait()
