import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

class AutomodService:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.blacklist_requesters_file = data_dir / "blacklist_requesters.json"
        self.blacklist_creators_file = data_dir / "blacklist_creators.json"
        self.blacklist_ids_file = data_dir / "blacklist_ids.json"
        self.played_file = data_dir / "played.json"
        
        self.blacklist_requesters = set()
        self.blacklist_creators = set()
        self.blacklist_ids = set()
        self.played = set()
        self.fucked_out_list = {'crash-trigger': [], 'nsfw': []}
        self.user_cooldowns = defaultdict(lambda: datetime.min)
        self.user_submissions = defaultdict(list)
        
        self.load_blacklists()
        self.load_played()
        self.fetch_fucked_out_list()
    
    def load_blacklists(self):
        # Load requesters
        if self.blacklist_requesters_file.exists():
            try:
                with open(self.blacklist_requesters_file, 'r', encoding='utf-8') as f:
                    self.blacklist_requesters = set(json.load(f))
            except:
                pass
        
        # Load creators
        if self.blacklist_creators_file.exists():
            try:
                with open(self.blacklist_creators_file, 'r', encoding='utf-8') as f:
                    self.blacklist_creators = set(json.load(f))
            except:
                pass
        
        # Load IDs
        if self.blacklist_ids_file.exists():
            try:
                with open(self.blacklist_ids_file, 'r', encoding='utf-8') as f:
                    self.blacklist_ids = set(json.load(f))
            except:
                pass
    
    def load_played(self):
        if self.played_file.exists():
            try:
                with open(self.played_file, 'r', encoding='utf-8') as f:
                    self.played = set(json.load(f))
            except:
                pass
    
    def fetch_fucked_out_list(self):
        try:
            url = "https://raw.githubusercontent.com/MalikHw/hwgdbot-db/main/fucked-out-list.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                self.fucked_out_list = response.json()
        except Exception as e:
            print(f"Failed to fetch fucked-out-list: {e}")
    
    def check_level(self, level_id: str, requester: str, platform: str) -> dict:
        level_id = str(level_id)
        
        # Check blacklisted requester
        if requester in self.blacklist_requesters:
            return {'allowed': False, 'reason': f'Requester {requester} is blacklisted'}
        
        # Check blacklisted ID
        if level_id in self.blacklist_ids:
            return {'allowed': False, 'reason': f'Level ID {level_id} is blacklisted'}
        
        # Check fucked-out list
        for category, entries in self.fucked_out_list.items():
            for entry in entries:
                if str(entry.get('level_id')) == level_id:
                    note = entry.get('note', 'This level is banned')
                    return {'allowed': False, 'reason': f'[{category}] {note}'}
        
        # Check if already played
        if level_id in self.played:
            return {'allowed': False, 'reason': 'Level already played this session'}
        
        # Check user cooldown (60 seconds)
        now = datetime.now()
        if now - self.user_cooldowns[requester] < timedelta(seconds=60):
            return {'allowed': False, 'reason': f'{requester} is on cooldown'}
        
        # Check same level spam (3 times = block)
        submissions = self.user_submissions[requester]
        submissions.append((level_id, now))
        
        # Clean old submissions (older than 5 minutes)
        self.user_submissions[requester] = [(lid, t) for lid, t in submissions 
                                            if now - t < timedelta(minutes=5)]
        
        # Count same level submissions
        same_level_count = sum(1 for lid, _ in self.user_submissions[requester] if lid == level_id)
        
        if same_level_count >= 3:
            return {'allowed': False, 'reason': f'{requester} spammed level {level_id} 3+ times'}
        
        # Update cooldown
        self.user_cooldowns[requester] = now
        
        return {'allowed': True, 'reason': None}
    
    def add_to_blacklist(self, list_type: str, value: str):
        value = str(value)
        
        if list_type == 'requester':
            self.blacklist_requesters.add(value)
            with open(self.blacklist_requesters_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.blacklist_requesters), f, indent=2)
        
        elif list_type == 'creator':
            self.blacklist_creators.add(value)
            with open(self.blacklist_creators_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.blacklist_creators), f, indent=2)
        
        elif list_type == 'id':
            self.blacklist_ids.add(value)
            with open(self.blacklist_ids_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.blacklist_ids), f, indent=2)
    
    def remove_from_blacklist(self, list_type: str, value: str):
        value = str(value)
        
        if list_type == 'requester':
            self.blacklist_requesters.discard(value)
            with open(self.blacklist_requesters_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.blacklist_requesters), f, indent=2)
        
        elif list_type == 'creator':
            self.blacklist_creators.discard(value)
            with open(self.blacklist_creators_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.blacklist_creators), f, indent=2)
        
        elif list_type == 'id':
            self.blacklist_ids.discard(value)
            with open(self.blacklist_ids_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.blacklist_ids), f, indent=2)
