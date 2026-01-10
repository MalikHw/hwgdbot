use std::fs;
use std::path::{Path, PathBuf};
use std::io::Write;
use chrono::Local;
use zip::write::FileOptions;
use zip::ZipWriter;

pub struct BackupManager;

impl BackupManager {
    pub fn get_backup_dir() -> PathBuf {
        let home = dirs::document_dir().unwrap_or_else(|| PathBuf::from("."));
        home.join("HwGDBot").join("backups")
    }
    
    pub fn create_backup() -> Result<String, String> {
        let backup_dir = Self::get_backup_dir();
        fs::create_dir_all(&backup_dir).map_err(|e| e.to_string())?;
        
        let timestamp = Local::now().format("%Y%m%d-%H%M%S");
        let backup_name = format!("backup-{}.hgb-bkp", timestamp);
        let backup_path = backup_dir.join(&backup_name);
        
        let file = fs::File::create(&backup_path).map_err(|e| e.to_string())?;
        let mut zip = ZipWriter::new(file);
        let options = FileOptions::default()
            .compression_method(zip::CompressionMethod::Deflated);
        
        // Add all JSON files from data folder
        let data_files = [
            "queue.json",
            "settings.json",
            "cache.json",
            "played.json",
            "blacklist_requesters.json",
            "blacklist_creators.json",
            "blacklist_ids.json",
        ];
        
        for file_name in &data_files {
            let file_path = format!("data/{}", file_name);
            if Path::new(&file_path).exists() {
                let content = fs::read(&file_path).map_err(|e| e.to_string())?;
                zip.start_file(file_name.to_string(), options)
                    .map_err(|e| e.to_string())?;
                zip.write_all(&content).map_err(|e| e.to_string())?;
            }
        }
        
        zip.finish().map_err(|e| e.to_string())?;
        
        // Clean old backups (keep only last 10)
        Self::cleanup_old_backups()?;
        
        Ok(backup_path.to_string_lossy().to_string())
    }
    
    pub fn restore_backup(backup_path: &str) -> Result<(), String> {
        let file = fs::File::open(backup_path).map_err(|e| e.to_string())?;
        let mut archive = zip::ZipArchive::new(file).map_err(|e| e.to_string())?;
        
        fs::create_dir_all("data").map_err(|e| e.to_string())?;
        
        for i in 0..archive.len() {
            let mut file = archive.by_index(i).map_err(|e| e.to_string())?;
            let outpath = format!("data/{}", file.name());
            
            let mut outfile = fs::File::create(&outpath).map_err(|e| e.to_string())?;
            std::io::copy(&mut file, &mut outfile).map_err(|e| e.to_string())?;
        }
        
        Ok(())
    }
    
    fn cleanup_old_backups() -> Result<(), String> {
        let backup_dir = Self::get_backup_dir();
        let mut backups: Vec<_> = fs::read_dir(&backup_dir)
            .map_err(|e| e.to_string())?
            .filter_map(|entry| entry.ok())
            .filter(|entry| {
                entry.path().extension()
                    .and_then(|s| s.to_str())
                    == Some("hgb-bkp")
            })
            .collect();
        
        if backups.len() <= 10 {
            return Ok(());
        }
        
        backups.sort_by_key(|entry| {
            entry.metadata()
                .and_then(|m| m.modified())
                .unwrap_or(std::time::SystemTime::UNIX_EPOCH)
        });
        
        let to_delete = backups.len() - 10;
        for entry in backups.iter().take(to_delete) {
            fs::remove_file(entry.path()).ok();
        }
        
        Ok(())
    }
    
    pub fn list_backups() -> Result<Vec<String>, String> {
        let backup_dir = Self::get_backup_dir();
        if !backup_dir.exists() {
            return Ok(Vec::new());
        }
        
        let backups: Vec<String> = fs::read_dir(&backup_dir)
            .map_err(|e| e.to_string())?
            .filter_map(|entry| entry.ok())
            .filter(|entry| {
                entry.path().extension()
                    .and_then(|s| s.to_str())
                    == Some("hgb-bkp")
            })
            .map(|entry| entry.path().to_string_lossy().to_string())
            .collect();
        
        Ok(backups)
    }
}

pub async fn start_auto_backup(interval_minutes: u64) {
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(tokio::time::Duration::from_secs(interval_minutes * 60)).await;
            if let Err(e) = BackupManager::create_backup() {
                eprintln!("Auto backup failed: {}", e);
            }
        }
    });
}