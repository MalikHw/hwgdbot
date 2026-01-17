import os
import json
import requests
from datetime import datetime, timedelta

DATA_DIR = "data"
CACHE_FILE = os.path.join(DATA_DIR, "cache.json")
CACHE_DURATION = timedelta(hours=24)

class GDIntegration:
    def __init__(self):
        self.api_url = "https://gdbrowser.com/api/level"
        self.cache = self.load_cache()
    
    def load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            from main import log
            log("ERROR", f"Failed to load cache: {e}")
        return {}
    
    def save_cache(self):
        """Save cache to file"""
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            from main import log
            log("ERROR", f"Failed to save cache: {e}")
    
    def is_cache_valid(self, level_id):
        """Check if cached data is still valid"""
        if str(level_id) not in self.cache:
            return False
        
        cached = self.cache[str(level_id)]
        cached_time = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
        
        return datetime.now() - cached_time < CACHE_DURATION
    
    def fetch_level(self, level_id):
        """Fetch level data from GDBrowser API or cache"""
        from main import log
        
        # Check cache first
        if self.is_cache_valid(level_id):
            log("INFO", f"Using cached data for level {level_id}")
            return self.cache[str(level_id)]["data"]
        
        # Fetch from API
        try:
            response = requests.get(f"{self.api_url}/{level_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if level exists (API returns -1 for non-existent levels)
                if data == -1 or (isinstance(data, dict) and data.get("error")):
                    log("WARNING", f"Level {level_id} not found")
                    return None
                
                # Parse level data
                level_data = self.parse_level_data(data)
                
                # Cache the result
                self.cache[str(level_id)] = {
                    "data": level_data,
                    "cached_at": datetime.now().isoformat()
                }
                self.save_cache()
                
                log("INFO", f"Fetched level {level_id} from API")
                return level_data
            else:
                log("ERROR", f"API returned status {response.status_code} for level {level_id}")
                return None
        
        except requests.exceptions.Timeout:
            log("ERROR", f"Timeout fetching level {level_id}")
            return None
        except Exception as e:
            log("ERROR", f"Error fetching level {level_id}: {e}")
            return None
    
    def parse_level_data(self, data):
        """Parse GDBrowser API response into our format"""
        # Difficulty mapping
        difficulty_map = {
            0: "auto",
            10: "easy",
            20: "normal",
            30: "hard",
            40: "harder",
            50: "insane"
        }
        
        # Get base difficulty
        difficulty_val = data.get("difficulty", 0)
        
        # Check if demon
        if data.get("isDemon") or data.get("demon"):
            demon_diff = data.get("demonDifficulty", 0)
            if demon_diff == 3:
                difficulty = "demon-easy"
            elif demon_diff == 4:
                difficulty = "demon-medium"
            elif demon_diff == 5:
                difficulty = "demon-insane"
            elif demon_diff == 6:
                difficulty = "demon-extreme"
            else:
                difficulty = "demon-hard"
        else:
            difficulty = difficulty_map.get(difficulty_val, "normal")
        
        # Difficulty face
        if data.get("difficulty") == "unrated":
            difficulty_face = "unrated"
        elif data.get("isDemon"):
            difficulty_face = "demon"
        else:
            difficulty_face = difficulty
        
        # Length mapping
        length_map = {
            0: "tiny",
            1: "short",
            2: "medium",
            3: "long",
            4: "xl"
        }
        length = length_map.get(data.get("length", 0), "medium")
        
        # Check if rated (has stars or featured)
        is_rated = (data.get("stars", 0) > 0) or data.get("featured", False) or data.get("epic", False)
        
        # Check if disliked (more dislikes than likes)
        likes = data.get("likes", 0)
        dislikes = data.get("dislikes", 0)
        is_disliked = dislikes > likes
        
        # Check if large (40k+ objects)
        objects = data.get("objects", 0)
        is_large = objects >= 40000
        
        # Get song name
        song = "Unknown"
        if data.get("songName"):
            song = data.get("songName")
        elif data.get("customSong"):
            song = data["customSong"].get("name", "Unknown")
        
        return {
            "level_id": data.get("id"),
            "level_name": data.get("name", "Unknown"),
            "author": data.get("author", "Unknown"),
            "song": song,
            "difficulty": difficulty,
            "difficultyFace": difficulty_face,
            "length": length,
            "downloads": data.get("downloads", 0),
            "likes": likes,
            "is_rated": is_rated,
            "is_disliked": is_disliked,
            "is_large": is_large
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache = {}
        self.save_cache()
        from main import log
        log("INFO", "Cache cleared")