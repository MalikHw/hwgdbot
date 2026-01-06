import json
from pathlib import Path
from datetime import datetime

class QueueManager:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.queue_file = data_dir / "queue.json"
        self.played_file = data_dir / "played.json"
        self.queue = []
        self.played = set()
        self.load_queue()
        self.load_played()
    
    def load_queue(self):
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    self.queue = json.load(f)
            except:
                self.queue = []
    
    def load_played(self):
        if self.played_file.exists():
            try:
                with open(self.played_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.played = set(data)
            except:
                self.played = set()
    
    def save_queue(self):
        with open(self.queue_file, 'w', encoding='utf-8') as f:
            json.dump(self.queue, f, indent=2, ensure_ascii=False)
    
    def save_played(self):
        with open(self.played_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.played), f, indent=2)
    
    def add_level(self, level_data: dict) -> bool:
        level_id = str(level_data['level_id'])
        
        # Check if already in queue
        if any(str(l['level_id']) == level_id for l in self.queue):
            return False
        
        # Add timestamp and attempts
        level_data['timestamp'] = datetime.now().isoformat()
        level_data['attempts'] = 0
        
        self.queue.append(level_data)
        self.save_queue()
        return True
    
    def remove_level(self, level_id: str):
        self.queue = [l for l in self.queue if str(l['level_id']) != str(level_id)]
        self.save_queue()
    
    def mark_played(self, level_id: str):
        self.played.add(str(level_id))
        self.save_played()
    
    def is_played(self, level_id: str) -> bool:
        return str(level_id) in self.played
    
    def get_queue(self) -> list:
        return self.queue.copy()
    
    def get_next_level(self) -> dict:
        return self.queue[0] if self.queue else None
    
    def increment_attempts(self, level_id: str):
        for level in self.queue:
            if str(level['level_id']) == str(level_id):
                level['attempts'] = level.get('attempts', 0) + 1
                self.save_queue()
                break
    
    def clear_queue(self):
        self.queue = []
        self.save_queue()
    
    def reset_played(self):
        self.played = set()
        self.save_played()
