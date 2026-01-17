import requests
import webbrowser
from PyQt6.QtWidgets import QMessageBox

VERSION_URL = "https://raw.githubusercontent.com/MalikHw/HwGDBot-db/main/ver.txt"
DOWNLOAD_URL = "https://malikhw.github.io/HwGDBot"

class UpdateChecker:
    def __init__(self, current_version):
        self.current_version = current_version
    
    def check_for_updates(self):
        """Check for updates from GitHub"""
        from main import log
        
        try:
            response = requests.get(VERSION_URL, timeout=10)
            
            if response.status_code == 200:
                latest_version = response.text.strip()
                
                log("INFO", f"Current version: {self.current_version}, Latest version: {latest_version}")
                
                if self.is_newer_version(latest_version):
                    self.show_update_dialog(latest_version)
                else:
                    log("INFO", "App is up to date")
        
        except Exception as e:
            log("WARNING", f"Failed to check for updates: {e}")
    
    def is_newer_version(self, latest_version):
        """Compare versions"""
        try:
            current_parts = [int(x) for x in self.current_version.split('.')]
            latest_parts = [int(x) for x in latest_version.split('.')]
            
            return latest_parts > current_parts
        except:
            return False
    
    def show_update_dialog(self, latest_version):
        """Show update available dialog"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Update Available")
        msg.setText(f"A new version of HwGDBot is available!")
        msg.setInformativeText(f"Current version: {self.current_version}\nLatest version: {latest_version}\n\nWould you like to download it?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        result = msg.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            webbrowser.open(DOWNLOAD_URL)
            
            from main import log
            log("INFO", "User chose to download update")