import re
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

class YouTubeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.url = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("YouTube Livestream URL")
        self.setFixedSize(500, 150)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Label
        label = QLabel("Enter your YouTube livestream URL:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=... or https://youtu.be/...")
        layout.addWidget(self.url_input)
        
        # Buttons
        ok_btn = QPushButton("Connect")
        ok_btn.clicked.connect(self.validate_and_accept)
        layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Skip")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        self.setLayout(layout)
    
    def validate_and_accept(self):
        """Validate URL and accept"""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Invalid URL", "Please enter a URL")
            return
        
        # Validate URL format
        patterns = [
            r'youtube\.com/watch\?v=[a-zA-Z0-9_-]{11}',
            r'youtu\.be/[a-zA-Z0-9_-]{11}',
            r'youtube\.com/live/[a-zA-Z0-9_-]{11}'
        ]
        
        valid = False
        for pattern in patterns:
            if re.search(pattern, url):
                valid = True
                break
        
        if not valid:
            QMessageBox.warning(
                self,
                "Invalid URL",
                "Invalid YouTube URL format.\n\n"
                "Accepted formats:\n"
                "• https://www.youtube.com/watch?v=VIDEO_ID\n"
                "• https://youtu.be/VIDEO_ID\n"
                "• https://www.youtube.com/live/VIDEO_ID"
            )
            return
        
        self.url = url
        self.accept()
    
    def get_url(self):
        """Get the entered URL"""
        return self.url