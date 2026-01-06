from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette
from pathlib import Path

class OBSOverlay(QWidget):
    def __init__(self, queue_manager, settings: dict):
        super().__init__()
        self.queue_manager = queue_manager
        self.settings = settings
        
        self.setWindowTitle("HwGDBot - OBS Overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        
        # Set size
        width = settings.get('obs_width', 600)
        height = settings.get('obs_height', 100)
        self.resize(width, height)
        
        # Set transparency
        transparency = settings.get('obs_transparency', 0)
        self.setWindowOpacity(1 - (transparency / 100))
        
        # Setup UI
        layout = QVBoxLayout()
        
        self.text_label = QLabel()
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        
        # Load custom font if specified
        font_path = settings.get('obs_font_path', '')
        if font_path and Path(font_path).exists():
            font_id = QFont.addApplicationFont(font_path)
            if font_id != -1:
                families = QFont.applicationFontFamilies(font_id)
                if families:
                    font = QFont(families[0], 20)
                    self.text_label.setFont(font)
        else:
            # Default font
            font = QFont()
            font.setPointSize(20)
            font.setBold(True)
            self.text_label.setFont(font)
        
        # Use system color palette
        palette = self.palette()
        self.text_label.setPalette(palette)
        
        layout.addWidget(self.text_label)
        self.setLayout(layout)
        
        self.update_display()
    
    def update_display(self):
        template = self.settings.get('obs_template', 'Next: {next-level} by {next-author}')
        queue = self.queue_manager.get_queue()
        
        if not queue:
            self.text_label.setText("Queue is empty")
            return
        
        current = queue[0] if len(queue) > 0 else None
        next_level = queue[1] if len(queue) > 1 else None
        
        # Replace variables
        text = template
        
        if current:
            text = text.replace('{level}', current['level_name'])
            text = text.replace('{author}', current['author'])
            text = text.replace('{id}', str(current['level_id']))
        
        if next_level:
            text = text.replace('{next-level}', next_level['level_name'])
            text = text.replace('{next-author}', next_level['author'])
        else:
            text = text.replace('{next-level}', 'None')
            text = text.replace('{next-author}', '')
        
        self.text_label.setText(text)
