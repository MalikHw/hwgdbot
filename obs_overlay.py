import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class OBSOverlay:
    def __init__(self, settings):
        self.settings = settings
        self.window = None
        self.server = None
        self.current_text = ""
        
        # Start HTTP server
        self.start_server()
        
        # Create window if enabled
        if settings.get("obs_overlay_window_enabled", False):
            self.create_window()
    
    def update_settings(self, settings):
        """Update settings"""
        self.settings = settings
        
        # Update window if exists
        if self.window:
            self.window.close()
            self.window = None
        
        if settings.get("obs_overlay_window_enabled", False):
            self.create_window()
            if self.current_text:
                self.update_text(self.current_text)
    
    def create_window(self):
        """Create overlay window"""
        self.window = QWidget()
        self.window.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set size
        width = self.settings.get("obs_overlay_width", 800)
        height = self.settings.get("obs_overlay_height", 100)
        self.window.resize(width, height)
        
        # Set transparency
        transparency = self.settings.get("obs_overlay_transparency", 100)
        self.window.setWindowOpacity(transparency / 100.0)
        
        # Layout
        layout = QVBoxLayout()
        self.window.setLayout(layout)
        
        # Label
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 180);")
        
        # Font
        font_path = self.settings.get("obs_overlay_font", "")
        if font_path and os.path.exists(font_path):
            font_id = QFont.addApplicationFont(font_path)
            if font_id != -1:
                font_family = QFont.applicationFontFamilies(font_id)[0]
                font = QFont(font_family, 16)
                self.label.setFont(font)
        else:
            self.label.setFont(QFont("Arial", 16))
        
        layout.addWidget(self.label)
        
        self.window.show()
    
    def start_server(self):
        """Start HTTP server for OBS Browser Source"""
        class OverlayHandler(BaseHTTPRequestHandler):
            overlay_instance = None
            
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                html = self.overlay_instance.generate_html()
                self.wfile.write(html.encode())
            
            def log_message(self, format, *args):
                pass  # Suppress log messages
        
        OverlayHandler.overlay_instance = self
        
        try:
            self.server = HTTPServer(("0.0.0.0", 6767), OverlayHandler)
            thread = Thread(target=self.server.serve_forever, daemon=True)
            thread.start()
            
            from main import log
            log("INFO", "OBS overlay server started on port 6767")
        except Exception as e:
            from main import log
            log("ERROR", f"Failed to start OBS overlay server: {e}")
    
    def generate_html(self):
        """Generate HTML for browser source"""
        template = self.settings.get("obs_overlay_template", "{level} by {author} (ID: {id})")
        font_path = self.settings.get("obs_overlay_font", "")
        width = self.settings.get("obs_overlay_width", 800)
        height = self.settings.get("obs_overlay_height", 100)
        transparency = self.settings.get("obs_overlay_transparency", 100)
        
        font_face = ""
        if font_path and os.path.exists(font_path):
            font_name = os.path.basename(font_path).replace(".ttf", "")
            font_face = f"""
            @font-face {{
                font-family: '{font_name}';
                src: url('file:///{font_path.replace(os.sep, "/")}');
            }}
            """
            font_family = font_name
        else:
            font_family = "Arial, sans-serif"
        
        bg_opacity = transparency / 100.0
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                {font_face}
                body {{
                    margin: 0;
                    padding: 0;
                    width: {width}px;
                    height: {height}px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background-color: rgba(0, 0, 0, {bg_opacity * 0.7});
                    font-family: {font_family};
                    color: white;
                    font-size: 24px;
                    text-align: center;
                }}
                #overlay {{
                    padding: 20px;
                }}
            </style>
        </head>
        <body>
            <div id="overlay">{self.current_text}</div>
            <script>
                setInterval(() => {{
                    fetch('/').then(r => r.text()).then(html => {{
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const newText = doc.getElementById('overlay').innerHTML;
                        if (newText !== document.getElementById('overlay').innerHTML) {{
                            document.getElementById('overlay').innerHTML = newText;
                        }}
                    }});
                }}, 1000);
            </script>
        </body>
        </html>
        """
        
        return html
    
    def update_overlay(self):
        """Update overlay with current queue"""
        from queue_manager import QueueManager
        
        # Get parent to access queue manager
        # This will be connected via signal, so we'll receive queue directly
        pass
    
    def format_text(self, queue):
        """Format text from queue"""
        if not queue:
            return "No levels in queue"
        
        template = self.settings.get("obs_overlay_template", "{level} by {author} (ID: {id})")
        
        current = queue[0] if len(queue) > 0 else None
        next_level = queue[1] if len(queue) > 1 else None
        
        text = template
        
        if current:
            text = text.replace("{level}", current.get("level_name", "Unknown"))
            text = text.replace("{author}", current.get("author", "Unknown"))
            text = text.replace("{id}", str(current.get("level_id", "0")))
        else:
            text = text.replace("{level}", "N/A")
            text = text.replace("{author}", "N/A")
            text = text.replace("{id}", "N/A")
        
        if next_level:
            text = text.replace("{next-level}", next_level.get("level_name", "Unknown"))
            text = text.replace("{next-author}", next_level.get("author", "Unknown"))
        else:
            text = text.replace("{next-level}", "N/A")
            text = text.replace("{next-author}", "N/A")
        
        return text
    
    def update_text(self, text):
        """Update displayed text"""
        self.current_text = text
        
        if self.window and hasattr(self, 'label'):
            self.label.setText(text)
    
    def close(self):
        """Close overlay"""
        if self.window:
            self.window.close()
        
        if self.server:
            self.server.shutdown()