import os
import json
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from gd_integration import GDIntegration

DATA_DIR = "data"

class QueueManager(QObject):
    queue_changed = pyqtSignal()
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.queue = []
        self.played = []
        self.accepting = True
        self.gd = GDIntegration()
        self.user_submissions = {}  # Track submissions per user per platform
        
        self.queue_path = os.path.join(DATA_DIR, "queue.json")
        self.played_path = os.path.join(DATA_DIR, "played.json")
        self.blacklist_requesters_path = os.path.join(DATA_DIR, "blacklist_requesters.json")
        self.blacklist_creators_path = os.path.join(DATA_DIR, "blacklist_creators.json")
        self.blacklist_ids_path = os.path.join(DATA_DIR, "blacklist_ids.json")
        
        self.blacklist_requesters = self.load_json(self.blacklist_requesters_path, [])
        self.blacklist_creators = self.load_json(self.blacklist_creators_path, [])
        self.blacklist_ids = self.load_json(self.blacklist_ids_path, [])
    
    def load_json(self, path, default):
        """Load JSON file or return default"""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            from main import log
            log("ERROR", f"Failed to load {path}: {e}")
        return default
    
    def save_json(self, path, data):
        """Save data to JSON file"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            from main import log
            log("ERROR", f"Failed to save {path}: {e}")
    
    def load_queue(self):
        """Load queue from file"""
        if self.settings.get("load_queue_on_start", True):
            self.queue = self.load_json(self.queue_path, [])
            self.queue_changed.emit()
            from main import log
            log("INFO", f"Loaded {len(self.queue)} levels from queue")
    
    def save_queue(self):
        """Save queue to file"""
        if self.settings.get("save_queue_on_change", True):
            self.save_json(self.queue_path, self.queue)
    
    def load_played(self):
        """Load played levels"""
        self.played = self.load_json(self.played_path, [])
    
    def save_played(self):
        """Save played levels"""
        self.save_json(self.played_path, self.played)
    
    def is_accepting(self):
        """Check if accepting new requests"""
        return self.accepting
    
    def set_accepting(self, accepting):
        """Set accepting state"""
        self.accepting = accepting
    
    def get_queue(self):
        """Get current queue"""
        return self.queue
    
    def add_level(self, level_id, requester, platform):
        """Add level to queue with all checks"""
        from main import log
        from automod_service import AutomodService
        
        # Check if level ID is already in queue
        if any(level['level_id'] == level_id for level in self.queue):
            return {"success": False, "reason": "Level already in queue"}
        
        # Check if requester is blacklisted
        requester_key = f"{requester}@{platform}"
        if requester_key in self.blacklist_requesters:
            return {"success": False, "reason": "Requester is blacklisted"}
        
        # Check if level ID is blacklisted
        if level_id in self.blacklist_ids:
            return {"success": False, "reason": "Level ID is blacklisted"}
        
        # Check max submissions per user
        max_ids = self.settings.get("max_ids_per_user", 0)
        if max_ids > 0:
            user_key = f"{requester}@{platform}"
            current_count = self.user_submissions.get(user_key, 0)
            if current_count >= max_ids:
                return {"success": False, "reason": f"Max {max_ids} submissions per user reached"}
        
        # Check per-user cooldown (will be implemented in automod)
        automod = AutomodService(self.settings)
        cooldown_result = automod.check_user_cooldown(requester, platform)
        if not cooldown_result["allowed"]:
            return {"success": False, "reason": cooldown_result.get("reason", "Cooldown active")}
        
        # Fetch level data from GDBrowser
        level_data = self.gd.fetch_level(level_id)
        if not level_data:
            return {"success": False, "reason": "Failed to fetch level data"}
        
        # Check if creator is blacklisted
        if level_data["author"] in self.blacklist_creators:
            return {"success": False, "reason": "Creator is blacklisted"}
        
        # Check same level same user
        if self.settings.get("block_same_level_same_user", True):
            user_key = f"{requester}@{platform}"
            if any(level['level_id'] == level_id and f"{level['requester']}@{level['platform']}" == user_key 
                   for level in self.queue):
                return {"success": False, "reason": "You already requested this level"}
        
        # Check if already played this session
        if self.settings.get("ignore_played", True):
            if level_id in self.played:
                return {"success": False, "reason": "Level already played this session"}
        
        # Check fucked-out-list
        is_fucked = False
        fucked_note = None
        if self.settings.get("reject_fucked_list", True):
            fucked_result = automod.check_fucked_list(level_id)
            if fucked_result["is_fucked"]:
                is_fucked = True
                fucked_note = fucked_result.get("note", "Unknown reason")
        
        # Check filters
        filter_result = self.check_filters(level_data)
        if not filter_result["allowed"]:
            return {"success": False, "reason": filter_result.get("reason", "Filtered out")}
        
        # Build level object
        level = {
            "level_id": level_id,
            "level_name": level_data["level_name"],
            "author": level_data["author"],
            "song": level_data["song"],
            "difficulty": level_data["difficulty"],
            "difficultyFace": level_data["difficultyFace"],
            "length": level_data["length"],
            "requester": requester,
            "platform": platform,
            "timestamp": datetime.now().isoformat(),
            "attempts": 0,
            "is_rated": level_data["is_rated"],
            "is_disliked": level_data["is_disliked"],
            "is_large": level_data["is_large"],
            "is_fucked": is_fucked,
            "fucked_note": fucked_note
        }
        
        # Add to queue
        self.queue.append(level)
        
        # Update submission count
        user_key = f"{requester}@{platform}"
        self.user_submissions[user_key] = self.user_submissions.get(user_key, 0) + 1
        
        # Save and emit
        self.save_queue()
        self.queue_changed.emit()
        
        log("INFO", f"Added level {level_id} to queue")
        
        return {"success": True}
    
    def check_filters(self, level_data):
        """Check if level passes filters"""
        # Length filter
        length_filters = self.settings.get("length_filters", {})
        if not length_filters.get(level_data["length"], True):
            return {"allowed": False, "reason": f"Length {level_data['length']} is filtered"}
        
        # Difficulty filter
        difficulty_filters = self.settings.get("difficulty_filters", {})
        if not difficulty_filters.get(level_data["difficulty"], True):
            return {"allowed": False, "reason": f"Difficulty {level_data['difficulty']} is filtered"}
        
        # Disliked filter
        if self.settings.get("block_disliked", False) and level_data["is_disliked"]:
            return {"allowed": False, "reason": "Level is disliked"}
        
        # Rated filter
        rated_filter = self.settings.get("rated_filter", "Any")
        if rated_filter == "Rated Only" and not level_data["is_rated"]:
            return {"allowed": False, "reason": "Level is not rated"}
        elif rated_filter == "Unrated Only" and level_data["is_rated"]:
            return {"allowed": False, "reason": "Level is rated"}
        
        # Large filter
        if self.settings.get("block_large", False) and level_data["is_large"]:
            return {"allowed": False, "reason": "Level is too large (40k+ objects)"}
        
        return {"allowed": True}
    
    def remove_level(self, level_id):
        """Remove level from queue"""
        self.queue = [level for level in self.queue if level['level_id'] != level_id]
        self.save_queue()
        self.queue_changed.emit()
    
    def mark_as_played(self, level_id):
        """Mark level as played and remove from queue"""
        self.played.append(level_id)
        self.save_played()
        self.remove_level(level_id)
    
    def delete_last_from_requester(self, requester, platform):
        """Delete last level from specific requester"""
        # Find last level from this requester
        for i in range(len(self.queue) - 1, -1, -1):
            level = self.queue[i]
            if level['requester'] == requester and level['platform'] == platform:
                self.queue.pop(i)
                
                # Decrement submission count
                user_key = f"{requester}@{platform}"
                if user_key in self.user_submissions:
                    self.user_submissions[user_key] -= 1
                    if self.user_submissions[user_key] <= 0:
                        del self.user_submissions[user_key]
                
                self.save_queue()
                self.queue_changed.emit()
                return True
        
        return False
    
    def ban_requester(self, requester, platform):
        """Ban a requester"""
        requester_key = f"{requester}@{platform}"
        if requester_key not in self.blacklist_requesters:
            self.blacklist_requesters.append(requester_key)
            self.save_json(self.blacklist_requesters_path, self.blacklist_requesters)
            
            # Remove all levels from this requester
            self.queue = [level for level in self.queue 
                         if not (level['requester'] == requester and level['platform'] == platform)]
            self.save_queue()
            self.queue_changed.emit()
    
    def ban_creator(self, creator):
        """Ban a creator"""
        if creator not in self.blacklist_creators:
            self.blacklist_creators.append(creator)
            self.save_json(self.blacklist_creators_path, self.blacklist_creators)
            
            # Remove all levels from this creator
            self.queue = [level for level in self.queue if level['author'] != creator]
            self.save_queue()
            self.queue_changed.emit()
    
    def ban_level_id(self, level_id):
        """Ban a level ID"""
        if level_id not in self.blacklist_ids:
            self.blacklist_ids.append(level_id)
            self.save_json(self.blacklist_ids_path, self.blacklist_ids)
            
            # Remove this level
            self.remove_level(level_id)
    
    def clear_queue(self):
        """Clear entire queue"""
        self.queue = []
        self.user_submissions = {}
        self.save_queue()
        self.queue_changed.emit()
    
    def reset_played(self):
        """Reset played levels list"""
        self.played = []
        self.save_played()