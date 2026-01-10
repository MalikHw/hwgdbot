use serde::{Deserialize, Serialize};
use std::fs;
use std::io;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    // Connection
    pub twitch_channel: String,
    pub twitch_token: String,
    pub youtube_enabled: bool,
    
    // Commands
    pub post_command: String,
    pub delete_command: String,
    pub max_ids_per_user: u32,
    
    // Automod
    pub block_duplicate_from_same_user: bool,
    pub reject_crash_nsfw: bool,
    pub ignore_played: bool,
    
    // Filters
    pub length_tiny: bool,
    pub length_short: bool,
    pub length_medium: bool,
    pub length_long: bool,
    pub length_xl: bool,
    
    pub diff_auto: bool,
    pub diff_easy: bool,
    pub diff_normal: bool,
    pub diff_hard: bool,
    pub diff_harder: bool,
    pub diff_insane: bool,
    pub diff_demon_easy: bool,
    pub diff_demon_medium: bool,
    pub diff_demon_hard: bool,
    pub diff_demon_insane: bool,
    pub diff_demon_extreme: bool,
    
    pub block_disliked: bool,
    pub rated_filter: String, // "any", "rated", "unrated"
    pub block_large: bool,
    
    // OBS Overlay
    pub overlay_enabled: bool,
    pub overlay_template: String,
    pub overlay_font: String,
    pub overlay_width: u32,
    pub overlay_height: u32,
    pub overlay_transparency: u32,
    pub overlay_color: String,
    
    // Sounds
    pub sounds_enabled: bool,
    pub sound_new_level: String,
    pub sound_error: String,
    
    // Backup
    pub backup_enabled: bool,
    pub backup_interval: u32,
    
    // Advanced
    pub save_queue_on_change: bool,
    pub load_queue_on_start: bool,
    
    // UI
    pub show_donation_popup: bool,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            twitch_channel: String::new(),
            twitch_token: String::new(),
            youtube_enabled: false,
            
            post_command: "!post".to_string(),
            delete_command: "!del".to_string(),
            max_ids_per_user: 0,
            
            block_duplicate_from_same_user: true,
            reject_crash_nsfw: true,
            ignore_played: false,
            
            length_tiny: true,
            length_short: true,
            length_medium: true,
            length_long: true,
            length_xl: true,
            
            diff_auto: true,
            diff_easy: true,
            diff_normal: true,
            diff_hard: true,
            diff_harder: true,
            diff_insane: true,
            diff_demon_easy: true,
            diff_demon_medium: true,
            diff_demon_hard: true,
            diff_demon_insane: true,
            diff_demon_extreme: true,
            
            block_disliked: false,
            rated_filter: "any".to_string(),
            block_large: false,
            
            overlay_enabled: false,
            overlay_template: "Now Playing: {level} by {author} (ID: {id})".to_string(),
            overlay_font: String::new(),
            overlay_width: 800,
            overlay_height: 100,
            overlay_transparency: 0,
            overlay_color: "#FFFFFF".to_string(),
            
            sounds_enabled: false,
            sound_new_level: String::new(),
            sound_error: String::new(),
            
            backup_enabled: false,
            backup_interval: 10,
            
            save_queue_on_change: true,
            load_queue_on_start: true,
            
            show_donation_popup: true,
        }
    }
}

impl Settings {
    pub fn load() -> io::Result<Self> {
        let data = fs::read_to_string("data/settings.json")?;
        let settings: Settings = serde_json::from_str(&data)?;
        Ok(settings)
    }
    
    pub fn save(&self) -> io::Result<()> {
        let data = serde_json::to_string_pretty(self)?;
        fs::write("data/settings.json", data)?;
        Ok(())
    }
}