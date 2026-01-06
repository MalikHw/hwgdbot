import requests

class UpdateChecker:
    def __init__(self):
        self.current_version = "1.0.0"  # Update this with each release
        self.latest_version = None
        self.check_url = "https://raw.githubusercontent.com/MalikHw/hwgdbot-db/main/ver.txt"
    
    def has_update(self) -> bool:
        try:
            response = requests.get(self.check_url, timeout=5)
            
            if response.status_code == 200:
                self.latest_version = response.text.strip()
                
                # Simple version comparison
                return self._compare_versions(self.current_version, self.latest_version) < 0
            
        except Exception as e:
            print(f"Update check failed: {e}")
        
        return False
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """Returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2"""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            for i in range(max(len(parts1), len(parts2))):
                p1 = parts1[i] if i < len(parts1) else 0
                p2 = parts2[i] if i < len(parts2) else 0
                
                if p1 < p2:
                    return -1
                elif p1 > p2:
                    return 1
            
            return 0
        except:
            return 0
