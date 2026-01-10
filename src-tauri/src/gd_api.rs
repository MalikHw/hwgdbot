use serde::{Deserialize, Serialize};
use std::fs;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GDLevel {
    pub id: String,
    pub name: String,
    pub author: String,
    pub song: String,
    pub difficulty: String,
    pub difficulty_face: String,
    pub length: String,
    pub downloads: u32,
    pub likes: i32,
    pub is_rated: bool,
    pub is_disliked: bool,
    pub is_large: bool,
}

#[derive(Debug, Deserialize)]
struct GDBrowserResponse {
    id: Option<i64>,
    name: Option<String>,
    #[serde(rename = "author")]
    creator: Option<String>,
    #[serde(rename = "songName")]
    song_name: Option<String>,
    difficulty: Option<String>,
    #[serde(rename = "difficultyFace")]
    difficulty_face: Option<String>,
    length: Option<String>,
    downloads: Option<i64>,
    likes: Option<i64>,
    stars: Option<i32>,
    #[serde(rename = "disliked")]
    disliked: Option<bool>,
    large: Option<bool>,
}

pub async fn fetch_level(level_id: &str) -> Result<GDLevel, Box<dyn std::error::Error>> {
    // Check cache first
    if let Ok(cached) = load_from_cache(level_id) {
        return Ok(cached);
    }
    
    // Fetch from GDBrowser
    let url = format!("https://gdbrowser.com/api/level/{}", level_id);
    let response = reqwest::get(&url).await?;
    
    if response.status() != 200 {
        return Err("Level not found".into());
    }
    
    let gd_response: GDBrowserResponse = response.json().await?;
    
    let level = GDLevel {
        id: gd_response.id.unwrap_or(0).to_string(),
        name: gd_response.name.unwrap_or_else(|| "Unknown".to_string()),
        author: gd_response.creator.unwrap_or_else(|| "Unknown".to_string()),
        song: gd_response.song_name.unwrap_or_else(|| "Unknown".to_string()),
        difficulty: normalize_difficulty(&gd_response.difficulty.unwrap_or_else(|| "Normal".to_string())),
        difficulty_face: gd_response.difficulty_face.unwrap_or_else(|| "normal".to_string()),
        length: normalize_length(&gd_response.length.unwrap_or_else(|| "Medium".to_string())),
        downloads: gd_response.downloads.unwrap_or(0) as u32,
        likes: gd_response.likes.unwrap_or(0) as i32,
        is_rated: gd_response.stars.unwrap_or(0) > 0,
        is_disliked: gd_response.disliked.unwrap_or(false),
        is_large: gd_response.large.unwrap_or(false),
    };
    
    // Save to cache
    save_to_cache(&level)?;
    
    Ok(level)
}

fn normalize_difficulty(diff: &str) -> String {
    match diff.to_lowercase().as_str() {
        "auto" => "auto".to_string(),
        "easy" => "easy".to_string(),
        "normal" => "normal".to_string(),
        "hard" => "hard".to_string(),
        "harder" => "harder".to_string(),
        "insane" => "insane".to_string(),
        "easy demon" => "demon-easy".to_string(),
        "medium demon" => "demon-medium".to_string(),
        "hard demon" => "demon-hard".to_string(),
        "insane demon" => "demon-insane".to_string(),
        "extreme demon" => "demon-extreme".to_string(),
        _ => "normal".to_string(),
    }
}

fn normalize_length(length: &str) -> String {
    match length.to_lowercase().as_str() {
        "tiny" => "tiny".to_string(),
        "short" => "short".to_string(),
        "medium" => "medium".to_string(),
        "long" => "long".to_string(),
        "xl" | "extra long" => "xl".to_string(),
        _ => "medium".to_string(),
    }
}

fn load_from_cache(level_id: &str) -> Result<GDLevel, Box<dyn std::error::Error>> {
    let cache_path = "data/cache.json";
    if !std::path::Path::new(cache_path).exists() {
        return Err("Cache not found".into());
    }
    
    let data = fs::read_to_string(cache_path)?;
    let cache: serde_json::Value = serde_json::from_str(&data)?;
    
    if let Some(level_data) = cache.get(level_id) {
        let level: GDLevel = serde_json::from_value(level_data.clone())?;
        Ok(level)
    } else {
        Err("Level not in cache".into())
    }
}

fn save_to_cache(level: &GDLevel) -> Result<(), Box<dyn std::error::Error>> {
    let cache_path = "data/cache.json";
    let mut cache: serde_json::Value = if std::path::Path::new(cache_path).exists() {
        let data = fs::read_to_string(cache_path)?;
        serde_json::from_str(&data)?
    } else {
        serde_json::json!({})
    };
    
    if let Some(cache_obj) = cache.as_object_mut() {
        cache_obj.insert(level.id.clone(), serde_json::to_value(level)?);
    }
    
    let data = serde_json::to_string_pretty(&cache)?;
    fs::write(cache_path, data)?;
    
    Ok(())
}