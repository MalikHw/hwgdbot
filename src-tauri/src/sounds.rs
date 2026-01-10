use std::time::{Duration, Instant};
use std::sync::Mutex;
use std::process::Command;

pub struct SoundManager {
    last_played: Mutex<Option<Instant>>,
}

impl SoundManager {
    pub fn new() -> Self {
        Self {
            last_played: Mutex::new(None),
        }
    }
    
    pub fn play_sound(&self, file_path: &str) -> Result<(), String> {
        let mut last = self.last_played.lock().map_err(|e| e.to_string())?;
        
        // Rate limit: max once every 2 seconds
        if let Some(last_time) = *last {
            if last_time.elapsed() < Duration::from_secs(2) {
                return Ok(()); // Skip this sound
            }
        }
        
        // Play sound based on platform
        #[cfg(target_os = "windows")]
        {
            self.play_sound_windows(file_path)?;
        }
        
        #[cfg(target_os = "linux")]
        {
            self.play_sound_linux(file_path)?;
        }
        
        *last = Some(Instant::now());
        Ok(())
    }
    
    #[cfg(target_os = "windows")]
    fn play_sound_windows(&self, file_path: &str) -> Result<(), String> {
        // Use PowerShell to play sound on Windows
        Command::new("powershell")
            .arg("-Command")
            .arg(format!(
                "(New-Object Media.SoundPlayer '{}').PlaySync()",
                file_path
            ))
            .spawn()
            .map_err(|e| format!("Failed to play sound: {}", e))?;
        Ok(())
    }
    
    #[cfg(target_os = "linux")]
    fn play_sound_linux(&self, file_path: &str) -> Result<(), String> {
        // Try different audio players on Linux
        let players = ["paplay", "aplay", "ffplay"];
        
        for player in &players {
            if let Ok(_) = Command::new(player)
                .arg(file_path)
                .spawn()
            {
                return Ok(());
            }
        }
        
        Err("No audio player found (tried paplay, aplay, ffplay)".to_string())
    }
}