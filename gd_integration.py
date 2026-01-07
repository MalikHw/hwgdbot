import requests
import json
from pathlib import Path

class GDIntegration:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.cache_file = data_dir / "cache.json"
        self.cache = {}
        self.load_cache()
        self.base_url = "https://gdbrowser.com/api"
    
    def load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
    
    def save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def fetch_level(self, level_id: str) -> dict:
        level_id = str(level_id).strip()
        
        # Check cache first
        if level_id in self.cache:
            return self.cache[level_id]
        
        try:
            response = requests.get(f"{self.base_url}/level/{level_id}", timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if isinstance(data, dict) and 'error' in data:
                return None
            
            # Map difficulty
            difficulty_map = {
                '0': 'auto',
                '10': 'easy',
                '20': 'normal',
                '30': 'hard',
                '40': 'harder',
                '50': 'insane',
                'demon': 'demon'
            }
            
            # Extract level info
            level_data = {
                'level_id': level_id,
                'level_name': data.get('name', 'Unknown'),
                'author': data.get('author', 'Unknown'),
                'song': self.get_song_info(data),
                'difficulty': self.get_difficulty(data),
                'length': self.get_length(data),
                'downloads': data.get('downloads', 0),
                'likes': data.get('likes', 0),
                'is_rated': bool(data.get('stars', 0) > 0 or data.get('featured', False)),
                'is_disliked': data.get('disliked', False),
                'is_large': data.get('large', False) or data.get('objects', 0) >= 40000
            }
            
            # Cache it
            self.cache[level_id] = level_data
            self.save_cache()
            
            return level_data
            
        except Exception as e:
            print(f"Error fetching level {level_id}: {e}")
            return None
    
    def get_song_info(self, data: dict) -> str:
        if 'songName' in data:
            return data['songName']
        if 'customSong' in data:
            return data['customSong']
        return "Unknown"
    
    def get_difficulty(self, data: dict) -> str:
        if data.get('difficulty') == 'Demon':
            # Check demon difficulty
            demon_diff = data.get('demonDifficulty', 0)
            if demon_diff == 3:
                return 'demon-easy'
            elif demon_diff == 4:
                return 'demon-medium'
            elif demon_diff == 5:
                return 'demon-insane'
            elif demon_diff == 6:
                return 'demon-extreme'
            else:
                return 'demon-hard'
        
        diff_face = data.get('difficultyFace', 'auto').lower()
        
        # Map common GDBrowser values
        mapping = {
            'auto': 'auto',
            'easy': 'easy',
            'normal': 'normal',
            'hard': 'hard',
            'harder': 'harder',
            'insane': 'insane',
            'demon': 'demon-hard',
            'extreme demon': 'demon-extreme',
            'insane demon': 'demon-insane',
            'medium demon': 'demon-medium',
            'easy demon': 'demon-easy',
            'hard demon': 'demon-hard'
        }
        
        return mapping.get(diff_face, 'normal')
    
    def get_length(self, data: dict) -> str:
        length_val = data.get('length', 0)
        
        # GD length values
        if length_val == 0:
            return 'tiny'
        elif length_val == 1:
            return 'short'
        elif length_val == 2:
            return 'medium'
        elif length_val == 3:
            return 'long'
        elif length_val == 4:
            return 'xl'
        
        return 'unknown'
    
    def clear_cache(self):
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
