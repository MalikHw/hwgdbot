from http.server import HTTPServer, BaseHTTPRequestHandler
from PyQt6.QtCore import QThread, pyqtSignal
import socket
import json

class OBSWebOverlay(QThread):
    server_started = pyqtSignal(str)  # Emits the URL
    
    def __init__(self, queue_manager, settings: dict, port: int = 8765):
        super().__init__()
        self.queue_manager = queue_manager
        self.settings = settings
        self.port = port
        self.running = False
        self.server = None
        
    def run(self):
        self.running = True
        
        # Create request handler with access to queue and settings
        overlay_instance = self
        
        class OverlayHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress server logs
            
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    html = overlay_instance.generate_html()
                    self.wfile.write(html.encode('utf-8'))
                
                elif self.path == '/data':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    data = overlay_instance.get_queue_data()
                    self.wfile.write(json.dumps(data).encode('utf-8'))
                
                else:
                    self.send_response(404)
                    self.end_headers()
        
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), OverlayHandler)
            
            # Get local IP
            local_ip = self.get_local_ip()
            url = f"http://{local_ip}:{self.port}"
            self.server_started.emit(url)
            
            while self.running:
                self.server.handle_request()
        
        except Exception as e:
            print(f"OBS Overlay server error: {e}")
        
        finally:
            if self.server:
                self.server.server_close()
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    def get_queue_data(self):
        """Get current queue data as JSON"""
        queue = self.queue_manager.get_queue()
        
        if not queue:
            return {'empty': True}
        
        current = queue[0] if len(queue) > 0 else None
        next_level = queue[1] if len(queue) > 1 else None
        
        return {
            'empty': False,
            'current': current,
            'next': next_level,
            'total': len(queue)
        }
    
    def generate_html(self):
        """Generate the HTML overlay page"""
        template = self.settings.get('obs_template', 'Next: {next-level} by {next-author}')
        font_size = self.settings.get('obs_font_size', 32)
        font_color = self.settings.get('obs_font_color', '#FFFFFF')
        font_family = self.settings.get('obs_font_family', 'Arial, sans-serif')
        text_shadow = self.settings.get('obs_text_shadow', True)
        text_align = self.settings.get('obs_text_align', 'center')
        animation = self.settings.get('obs_animation', 'fade')
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HwGDBot OBS Overlay</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            background: transparent;
            font-family: {font_family};
            overflow: hidden;
        }}
        
        #overlay {{
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: {text_align};
            padding: 20px;
        }}
        
        #text {{
            font-size: {font_size}px;
            color: {font_color};
            font-weight: bold;
            text-align: {text_align};
            max-width: 90%;
            word-wrap: break-word;
            {'text-shadow: 2px 2px 4px rgba(0,0,0,0.8), -1px -1px 2px rgba(0,0,0,0.8);' if text_shadow else ''}
            opacity: 0;
            transition: opacity 0.5s ease-in-out;
        }}
        
        #text.visible {{
            opacity: 1;
        }}
        
        #text.fade {{
            animation: fadeIn 0.5s ease-in-out forwards;
        }}
        
        #text.slide {{
            animation: slideIn 0.5s ease-out forwards;
        }}
        
        #text.bounce {{
            animation: bounceIn 0.6s ease-out forwards;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        @keyframes slideIn {{
            from {{ 
                opacity: 0;
                transform: translateX(-50px);
            }}
            to {{ 
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        @keyframes bounceIn {{
            0% {{ 
                opacity: 0;
                transform: scale(0.3);
            }}
            50% {{ 
                transform: scale(1.05);
            }}
            70% {{ 
                transform: scale(0.9);
            }}
            100% {{ 
                opacity: 1;
                transform: scale(1);
            }}
        }}
    </style>
</head>
<body>
    <div id="overlay">
        <div id="text">Loading...</div>
    </div>
    
    <script>
        const template = `{template}`;
        const animation = '{animation}';
        let lastData = null;
        
        function updateOverlay() {{
            fetch('/data')
                .then(res => res.json())
                .then(data => {{
                    const textEl = document.getElementById('text');
                    
                    if (data.empty) {{
                        if (lastData && !lastData.empty) {{
                            // Queue just became empty
                            textEl.classList.remove('visible', animation);
                            setTimeout(() => {{
                                textEl.textContent = 'Queue is empty';
                                textEl.classList.add('visible', animation);
                            }}, 100);
                        }} else {{
                            textEl.textContent = 'Queue is empty';
                            textEl.classList.add('visible');
                        }}
                        lastData = data;
                        return;
                    }}
                    
                    let text = template;
                    
                    // Replace current level variables
                    if (data.current) {{
                        text = text.replace(/{{level}}/g, data.current.level_name);
                        text = text.replace(/{{author}}/g, data.current.author);
                        text = text.replace(/{{id}}/g, data.current.level_id);
                        text = text.replace(/{{requester}}/g, data.current.requester);
                    }}
                    
                    // Replace next level variables
                    if (data.next) {{
                        text = text.replace(/{{next-level}}/g, data.next.level_name);
                        text = text.replace(/{{next-author}}/g, data.next.author);
                        text = text.replace(/{{next-id}}/g, data.next.level_id);
                        text = text.replace(/{{next-requester}}/g, data.next.requester);
                    }} else {{
                        text = text.replace(/{{next-level}}/g, 'None');
                        text = text.replace(/{{next-author}}/g, '');
                        text = text.replace(/{{next-id}}/g, '');
                        text = text.replace(/{{next-requester}}/g, '');
                    }}
                    
                    // Replace queue count
                    text = text.replace(/{{count}}/g, data.total);
                    
                    // Check if data changed
                    const dataStr = JSON.stringify(data);
                    if (dataStr !== JSON.stringify(lastData)) {{
                        // Animate change
                        textEl.classList.remove('visible', animation);
                        setTimeout(() => {{
                            textEl.textContent = text;
                            textEl.classList.add('visible', animation);
                        }}, 100);
                    }} else {{
                        textEl.textContent = text;
                        textEl.classList.add('visible');
                    }}
                    
                    lastData = data;
                }})
                .catch(err => {{
                    console.error('Failed to fetch data:', err);
                }});
        }}
        
        // Update every 2 seconds
        updateOverlay();
        setInterval(updateOverlay, 2000);
    </script>
</body>
</html>'''
        return html
    
    def stop(self):
        self.running = False
        if self.server:
            self.server.shutdown()
        self.wait()