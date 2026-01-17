import os
import json
import requests
from datetime import datetime, timedelta

DATA_DIR = "data"
FUCKED_LIST_URL = "https://raw.githubusercontent.com/MalikHw/HwGDBot-db/main/fucked-out-list.json"
FUCKED_LIST_FILE = os.path.join(DATA_DIR, "fucked-out-list.json")

class AutomodService:
    def __init__(self, settings):
        self.settings = settings
        self.user_cooldowns = {}
        self.fucked_list = self.load_fucked_list()
    
    def update_settings(self, settings):
        """Update settings"""
        self.settings = settings
    
    def load_fucked_list(self):
        """Load fucked-out-list from GitHub or local cache"""
        from main import log
        
        try:
            # Try to fetch from GitHub
            response = requests.get(FUCKED_LIST_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Save to local cache
                with open(FUCKED_LIST_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                log("INFO", "Downloaded fucked-out-list from GitHub")
                return data
        except Exception as e:
            log("WARNING", f"Failed to download fucked-out-list: {e}")
        
        # Fall back to local cache
        try:
            if os.path.exists(FUCKED_LIST_FILE):
                with open(FUCKED_LIST_FILE, "r", encoding="utf-8") as f:
                    log("INFO", "Using cached fucked-out-list")
                    return json.load(f)
        except Exception as e:
            log("ERROR", f"Failed to load cached fucked-out-list: {e}")
        
        return {}
    
    def check_user_cooldown(self, requester, platform):
        """Check if user is on cooldown"""
        if not self.settings.get("per_user_cooldown", True):
            return {"allowed": True}
        
        user_key = f"{requester}@{platform}"
        
        if user_key in self.user_cooldowns:
            last_request = self.user_cooldowns[user_key]
            elapsed = (datetime.now() - last_request).total_seconds()
            
            if elapsed < 60:
                return {
                    "allowed": False,
                    "reason": f"Cooldown active ({int(60 - elapsed)}s remaining)"
                }
        
        # Update cooldown
        self.user_cooldowns[user_key] = datetime.now()
        return {"allowed": True}
    
    def check_fucked_list(self, level_id):
        """Check if level is in fucked-out-list"""
        if not self.settings.get("reject_fucked_list", True):
            return {"is_fucked": False}
        
        # Check crash-trigger category
        crash_levels = self.fucked_list.get("crash-trigger", [])
        for entry in crash_levels:
            if str(entry.get("level_id")) == str(level_id):
                return {
                    "is_fucked": True,
                    "category": "crash-trigger",
                    "note": entry.get("note", "Crash trigger")
                }
        
        # Check nsfw category
        nsfw_levels = self.fucked_list.get("nsfw", [])
        for entry in nsfw_levels:
            if str(entry.get("level_id")) == str(level_id):
                return {
                    "is_fucked": True,
                    "category": "nsfw",
                    "note": entry.get("note", "NSFW content")
                }
        
        return {"is_fucked": False}
    
    def reload_fucked_list(self):
        """Reload fucked-out-list from GitHub"""
        self.fucked_list = self.load_fucked_list()