import requests
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt

REPORT_URL = "https://hwgdbot.rf.gd/fuckit.php"

class ReportDialog(QDialog):
    def __init__(self, level, settings):
        super().__init__()
        self.level = level
        self.settings = settings
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Report Level")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Level info
        info_label = QLabel(f"<b>Level:</b> {self.level['level_name']}<br>"
                           f"<b>ID:</b> {self.level['level_id']}<br>"
                           f"<b>Author:</b> {self.level['author']}<br>"
                           f"<b>Requester:</b> {self.level['requester']} ({self.level['platform']})")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Reason input
        reason_label = QLabel("Reason (required):")
        layout.addWidget(reason_label)
        
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("Describe why this level should be flagged...")
        layout.addWidget(self.reason_input)
        
        # Ban checkbox (only for Twitch)
        self.ban_checkbox = None
        if self.level['platform'] == 'twitch':
            self.ban_checkbox = QCheckBox(f"Ban {self.level['requester']} from my Twitch channel")
            self.ban_checkbox.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(self.ban_checkbox)
        
        # Buttons
        submit_btn = QPushButton("Submit Report")
        submit_btn.clicked.connect(self.submit_report)
        layout.addWidget(submit_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        self.setLayout(layout)
    
    def submit_report(self):
        """Submit the report"""
        from main import log
        
        reason = self.reason_input.toPlainText().strip()
        
        if not reason:
            QMessageBox.warning(self, "Error", "Please provide a reason for the report")
            return
        
        reporter = self.settings.get("streamer_name", "Anonymous")
        
        # Prepare data
        data = {
            "level_id": self.level['level_id'],
            "level_name": self.level['level_name'],
            "author": self.level['author'],
            "reason": reason,
            "reporter": reporter
        }
        
        try:
            # Submit report
            response = requests.post(REPORT_URL, data=data, timeout=10)
            
            if response.status_code == 200:
                log("INFO", f"Report submitted for level {self.level['level_id']}")
                
                # Ban user if checkbox is checked
                if self.ban_checkbox and self.ban_checkbox.isChecked():
                    self.ban_twitch_user()
                
                QMessageBox.information(self, "Success", "Report submitted successfully!")
                self.accept()
            else:
                log("ERROR", f"Failed to submit report: HTTP {response.status_code}")
                QMessageBox.warning(self, "Error", f"Failed to submit report (HTTP {response.status_code})")
        
        except Exception as e:
            log("ERROR", f"Error submitting report: {e}")
            QMessageBox.warning(self, "Error", f"Failed to submit report: {e}")
    
    def ban_twitch_user(self):
        """Ban user from Twitch channel"""
        from main import log
        
        try:
            # Get parent window to access Twitch service
            parent = self.parent()
            if parent and hasattr(parent, 'twitch_service') and parent.twitch_service:
                parent.twitch_service.ban_user(self.level['requester'])
                log("INFO", f"Banned {self.level['requester']} from Twitch channel")
        except Exception as e:
            log("ERROR", f"Failed to ban Twitch user: {e}")