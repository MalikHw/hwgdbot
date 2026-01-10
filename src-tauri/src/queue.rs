use serde::{Deserialize, Serialize};
use std::fs;
use std::io;
use std::collections::HashMap;
use crate::settings::Settings;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Level {
    pub level_id: String,
    pub level_name: String,
    pub author: String,
    pub song: String,
    pub difficulty: String,
    pub difficulty_face: String,
    pub length: String,
    pub requester: String,
    pub platform: String,
    pub timestamp: i64,
    pub attempts: u32,
    pub is_rated: bool,
    pub is_disliked: bool,
    pub is_large: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Queue {
    pub levels: Vec<Level>,
    #[serde(skip)]
    pub submission_counts: HashMap<String, u32>,
}

impl Default for Queue {
    fn default() -> Self {
        Self {
            levels: Vec::new(),
            submission_counts: HashMap::new(),
        }
    }
}

impl Queue {
    pub fn load() -> io::Result<Self> {
        let data = fs::read_to_string("data/queue.json")?;
        let mut queue: Queue = serde_json::from_str(&data)?;
        queue.submission_counts = HashMap::new();
        Ok(queue)
    }
    
    pub fn save(&self) -> io::Result<()> {
        let data = serde_json::to_string_pretty(&self.levels)?;
        fs::write("data/queue.json", data)?;
        Ok(())
    }
    
    pub fn add_level(&mut self, level: Level, settings: &Settings) -> Result<(), String> {
        // Check if level already in queue
        if self.levels.iter().any(|l| l.level_id == level.level_id) {
            return Err("Level already in queue".to_string());
        }
        
        // Check max submissions per user
        if settings.max_ids_per_user > 0 {
            let count = self.submission_counts.entry(level.requester.clone()).or_insert(0);
            if *count >= settings.max_ids_per_user {
                return Err(format!("User has reached max submissions ({})", settings.max_ids_per_user));
            }
            *count += 1;
        }
        
        // Check if already played
        if settings.ignore_played && self.is_played(&level.level_id)? {
            return Err("Level already played this session".to_string());
        }
        
        // Check duplicate from same user
        if settings.block_duplicate_from_same_user {
            if self.levels.iter().any(|l| l.requester == level.requester && l.level_id == level.level_id) {
                return Err("User already requested this level".to_string());
            }
        }
        
        // Check length filter
        let length_allowed = match level.length.as_str() {
            "tiny" => settings.length_tiny,
            "short" => settings.length_short,
            "medium" => settings.length_medium,
            "long" => settings.length_long,
            "xl" => settings.length_xl,
            _ => true,
        };
        if !length_allowed {
            return Err(format!("Length '{}' is filtered", level.length));
        }
        
        // Check difficulty filter
        let diff_allowed = match level.difficulty.as_str() {
            "auto" => settings.diff_auto,
            "easy" => settings.diff_easy,
            "normal" => settings.diff_normal,
            "hard" => settings.diff_hard,
            "harder" => settings.diff_harder,
            "insane" => settings.diff_insane,
            "demon-easy" => settings.diff_demon_easy,
            "demon-medium" => settings.diff_demon_medium,
            "demon-hard" => settings.diff_demon_hard,
            "demon-insane" => settings.diff_demon_insane,
            "demon-extreme" => settings.diff_demon_extreme,
            _ => true,
        };
        if !diff_allowed {
            return Err(format!("Difficulty '{}' is filtered", level.difficulty));
        }
        
        // Check disliked filter
        if settings.block_disliked && level.is_disliked {
            return Err("Disliked levels are filtered".to_string());
        }
        
        // Check rated filter
        match settings.rated_filter.as_str() {
            "rated" => {
                if !level.is_rated {
                    return Err("Only rated levels allowed".to_string());
                }
            }
            "unrated" => {
                if level.is_rated {
                    return Err("Only unrated levels allowed".to_string());
                }
            }
            _ => {}
        }
        
        // Check large filter
        if settings.block_large && level.is_large {
            return Err("Large levels (40k+ objects) are filtered".to_string());
        }
        
        // Check blacklists
        if self.is_blacklisted("requesters", &level.requester)? {
            return Err(format!("Requester '{}' is blacklisted", level.requester));
        }
        if self.is_blacklisted("creators", &level.author)? {
            return Err(format!("Creator '{}' is blacklisted", level.author));
        }
        if self.is_blacklisted("ids", &level.level_id)? {
            return Err(format!("Level ID '{}' is blacklisted", level.level_id));
        }
        
        // Check fucked-out-list (crash/NSFW)
        if settings.reject_crash_nsfw {
            if self.is_in_fucked_list(&level.level_id)? {
                return Err("Level is in crash/NSFW database".to_string());
            }
        }
        
        self.levels.push(level);
        Ok(())
    }
    
    pub fn add_to_played(&self, level: &Level) -> io::Result<()> {
        let mut played = self.load_played()?;
        played.push(level.clone());
        let data = serde_json::to_string_pretty(&played)?;
        fs::write("data/played.json", data)?;
        Ok(())
    }
    
    fn load_played(&self) -> io::Result<Vec<Level>> {
        if !std::path::Path::new("data/played.json").exists() {
            return Ok(Vec::new());
        }
        let data = fs::read_to_string("data/played.json")?;
        let played: Vec<Level> = serde_json::from_str(&data)?;
        Ok(played)
    }
    
    fn is_played(&self, level_id: &str) -> Result<bool, String> {
        let played = self.load_played().map_err(|e| e.to_string())?;
        Ok(played.iter().any(|l| l.level_id == level_id))
    }
    
    pub fn add_to_blacklist(&self, blacklist_type: &str, value: &str) -> io::Result<()> {
        let filename = format!("data/blacklist_{}.json", blacklist_type);
        let mut list = self.load_blacklist_file(&filename)?;
        if !list.contains(&value.to_string()) {
            list.push(value.to_string());
        }
        let data = serde_json::to_string_pretty(&list)?;
        fs::write(&filename, data)?;
        Ok(())
    }
    
    pub fn get_blacklist(&self, blacklist_type: &str) -> io::Result<Vec<String>> {
        let filename = format!("data/blacklist_{}.json", blacklist_type);
        self.load_blacklist_file(&filename)
    }
    
    fn load_blacklist_file(&self, filename: &str) -> io::Result<Vec<String>> {
        if !std::path::Path::new(filename).exists() {
            return Ok(Vec::new());
        }
        let data = fs::read_to_string(filename)?;
        let list: Vec<String> = serde_json::from_str(&data)?;
        Ok(list)
    }
    
    fn is_blacklisted(&self, blacklist_type: &str, value: &str) -> Result<bool, String> {
        let list = self.get_blacklist(blacklist_type).map_err(|e| e.to_string())?;
        Ok(list.contains(&value.to_string()))
    }
    
    fn is_in_fucked_list(&self, level_id: &str) -> Result<bool, String> {
        // Load fucked-out-list from cache or fetch from GitHub
        let cache_path = "data/fucked-out-list.json";
        let data = if std::path::Path::new(cache_path).exists() {
            fs::read_to_string(cache_path).map_err(|e| e.to_string())?
        } else {
            // Fetch from GitHub on first use
            return Ok(false); // For now, return false if not cached
        };
        
        let fucked_list: serde_json::Value = serde_json::from_str(&data).map_err(|e| e.to_string())?;
        if let Some(categories) = fucked_list.as_object() {
            for (_, levels) in categories {
                if let Some(levels_array) = levels.as_array() {
                    for level_entry in levels_array {
                        if let Some(id) = level_entry.get("level_id") {
                            if id.as_str() == Some(level_id) {
                                return Ok(true);
                            }
                        }
                    }
                }
            }
        }
        Ok(false)
    }
}