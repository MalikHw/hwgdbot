import os
import json
import zipfile
import shutil
import platform
from datetime import datetime
from pathlib import Path

DATA_DIR = "data"

class BackupService:
    def __init__(self):
        self.backup_dir = self.get_backup_dir()
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def get_backup_dir(self):
        """Get backup directory path"""
        if platform.system() == "Windows":
            docs = Path.home() / "Documents"
        else:
            docs = Path.home()
        
        backup_path = docs / "HwGDBot"
        return str(backup_path)
    
    def create_backup(self):
        """Create a backup of all JSON files"""
        from main import log
        
        try:
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_filename = f"backup-{timestamp}.hgb-bkp"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Create ZIP file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all JSON files from data folder
                if os.path.exists(DATA_DIR):
                    for filename in os.listdir(DATA_DIR):
                        if filename.endswith('.json'):
                            file_path = os.path.join(DATA_DIR, filename)
                            zipf.write(file_path, filename)
            
            log("INFO", f"Backup created: {backup_filename}")
            
            # Clean old backups (keep only last 10)
            self.clean_old_backups()
            
            return True
        
        except Exception as e:
            log("ERROR", f"Failed to create backup: {e}")
            return False
    
    def clean_old_backups(self):
        """Keep only the last 10 backups"""
        from main import log
        
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.hgb-bkp'):
                    file_path = os.path.join(self.backup_dir, filename)
                    backups.append((file_path, os.path.getmtime(file_path)))
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Delete old backups (keep only 10)
            for file_path, _ in backups[10:]:
                os.remove(file_path)
                log("INFO", f"Deleted old backup: {os.path.basename(file_path)}")
        
        except Exception as e:
            log("ERROR", f"Failed to clean old backups: {e}")
    
    def restore_backup(self, backup_path):
        """Restore from a backup file"""
        from main import log
        
        try:
            if not os.path.exists(backup_path):
                log("ERROR", f"Backup file not found: {backup_path}")
                return False
            
            # Extract ZIP to data folder
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(DATA_DIR)
            
            log("INFO", f"Backup restored from: {os.path.basename(backup_path)}")
            return True
        
        except Exception as e:
            log("ERROR", f"Failed to restore backup: {e}")
            return False
    
    def open_backup_folder(self):
        """Open backup folder in file explorer"""
        import subprocess
        
        try:
            if platform.system() == "Windows":
                os.startfile(self.backup_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.backup_dir])
            else:  # Linux
                subprocess.run(["xdg-open", self.backup_dir])
        except Exception as e:
            from main import log
            log("ERROR", f"Failed to open backup folder: {e}")