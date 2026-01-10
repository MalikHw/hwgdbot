#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod twitch;
mod gd_api;
mod queue;
mod settings;
mod youtube;
mod overlay;
mod sounds;
mod backup;
mod logger;

use tauri::{CustomMenuItem, SystemTray, SystemTrayMenu, SystemTrayEvent, Manager, Window};
use std::sync::{Arc, Mutex};
use tauri::State;

struct AppState {
    queue: Arc<Mutex<queue::Queue>>,
    settings: Arc<Mutex<settings::Settings>>,
    twitch_handle: Mutex<Option<tokio::task::JoinHandle<()>>>,
    youtube_handle: Mutex<Option<std::process::Child>>,
    overlay_handle: Mutex<Option<tokio::task::JoinHandle<()>>>,
    sound_manager: Arc<sounds::SoundManager>,
    backup_handle: Mutex<Option<tokio::task::JoinHandle<()>>>,
}

#[tauri::command]
fn get_queue(state: State<AppState>) -> Result<Vec<queue::Level>, String> {
    let queue = state.queue.lock().map_err(|e| e.to_string())?;
    Ok(queue.levels.clone())
}

#[tauri::command]
fn remove_level(state: State<AppState>, index: usize) -> Result<(), String> {
    let mut queue = state.queue.lock().map_err(|e| e.to_string())?;
    if index < queue.levels.len() {
        queue.levels.remove(index);
        queue.save().map_err(|e| e.to_string())?;
        log_info!("Removed level at index {}", index);
        Ok(())
    } else {
        Err("Index out of bounds".to_string())
    }
}

#[tauri::command]
fn mark_played(state: State<AppState>, index: usize) -> Result<(), String> {
    let mut queue = state.queue.lock().map_err(|e| e.to_string())?;
    if index < queue.levels.len() {
        let level = queue.levels.remove(index);
        log_info!("Marked level as played: {} ({})", level.level_name, level.level_id);
        queue.add_to_played(&level).map_err(|e| e.to_string())?;
        queue.save().map_err(|e| e.to_string())?;
        Ok(())
    } else {
        Err("Index out of bounds".to_string())
    }
}

#[tauri::command]
fn copy_level_id(state: State<AppState>, index: usize) -> Result<String, String> {
    let queue = state.queue.lock().map_err(|e| e.to_string())?;
    if index < queue.levels.len() {
        Ok(queue.levels[index].level_id.clone())
    } else {
        Err("Index out of bounds".to_string())
    }
}

#[tauri::command]
fn get_settings(state: State<AppState>) -> Result<settings::Settings, String> {
    let settings = state.settings.lock().map_err(|e| e.to_string())?;
    Ok(settings.clone())
}

#[tauri::command]
fn save_settings(state: State<AppState>, new_settings: settings::Settings) -> Result<(), String> {
    let mut settings = state.settings.lock().map_err(|e| e.to_string())?;
    *settings = new_settings;
    settings.save().map_err(|e| e.to_string())?;
    log_info!("Settings saved");
    Ok(())
}

#[tauri::command]
async fn start_twitch(state: State<'_, AppState>, window: Window) -> Result<(), String> {
    let settings = state.settings.lock().map_err(|e| e.to_string())?;
    let channel = settings.twitch_channel.clone();
    let token = settings.twitch_token.clone();
    let post_cmd = settings.post_command.clone();
    let del_cmd = settings.delete_command.clone();
    drop(settings);

    if channel.is_empty() || token.is_empty() {
        return Err("Twitch channel or token not configured".to_string());
    }

    log_info!("Starting Twitch bot for channel: {}", channel);
    let handle = tokio::spawn(async move {
        twitch::start_twitch_bot(channel, token, post_cmd, del_cmd, window).await;
    });

    let mut twitch_handle = state.twitch_handle.lock().map_err(|e| e.to_string())?;
    *twitch_handle = Some(handle);

    Ok(())
}

#[tauri::command]
async fn stop_twitch(state: State<'_, AppState>) -> Result<(), String> {
    let mut handle = state.twitch_handle.lock().map_err(|e| e.to_string())?;
    if let Some(h) = handle.take() {
        h.abort();
        log_info!("Stopped Twitch bot");
    }
    Ok(())
}

#[tauri::command]
async fn start_youtube(state: State<'_, AppState>, video_id: String, window: Window) -> Result<(), String> {
    let settings = state.settings.lock().map_err(|e| e.to_string())?;
    let post_cmd = settings.post_command.clone();
    let del_cmd = settings.delete_command.clone();
    drop(settings);

    log_info!("Starting YouTube bot for video: {}", video_id);
    let child = youtube::start_youtube_bot(video_id, post_cmd, del_cmd, window)
        .map_err(|e| e.to_string())?;

    let mut youtube_handle = state.youtube_handle.lock().map_err(|e| e.to_string())?;
    *youtube_handle = Some(child);

    Ok(())
}

#[tauri::command]
async fn stop_youtube(state: State<'_, AppState>) -> Result<(), String> {
    let mut handle = state.youtube_handle.lock().map_err(|e| e.to_string())?;
    if let Some(mut child) = handle.take() {
        let _ = child.kill();
        log_info!("Stopped YouTube bot");
    }
    Ok(())
}

#[tauri::command]
async fn fetch_level(level_id: String) -> Result<gd_api::GDLevel, String> {
    log_info!("Fetching level: {}", level_id);
    gd_api::fetch_level(&level_id).await.map_err(|e| e.to_string())
}

#[tauri::command]
fn add_level_to_queue(state: State<AppState>, level: queue::Level) -> Result<(), String> {
    let mut queue = state.queue.lock().map_err(|e| e.to_string())?;
    let settings = state.settings.lock().map_err(|e| e.to_string())?;
    
    match queue.add_level(level.clone(), &settings) {
        Ok(_) => {
            log_info!("Added level to queue: {} ({})", level.level_name, level.level_id);
            
            // Play sound if enabled
            if settings.sounds_enabled && !settings.sound_new_level.is_empty() {
                if let Err(e) = state.sound_manager.play_sound(&settings.sound_new_level) {
                    log_warn!("Failed to play sound: {}", e);
                }
            }
            
            if settings.save_queue_on_change {
                queue.save().map_err(|e| e.to_string())?;
            }
            Ok(())
        }
        Err(e) => {
            log_warn!("Failed to add level: {}", e);
            
            // Play error sound if enabled
            if settings.sounds_enabled && !settings.sound_error.is_empty() {
                if let Err(e) = state.sound_manager.play_sound(&settings.sound_error) {
                    log_warn!("Failed to play error sound: {}", e);
                }
            }
            
            Err(e)
        }
    }
}

#[tauri::command]
fn add_to_blacklist(state: State<AppState>, blacklist_type: String, value: String) -> Result<(), String> {
    let queue = state.queue.lock().map_err(|e| e.to_string())?;
    log_info!("Added to {} blacklist: {}", blacklist_type, value);
    queue.add_to_blacklist(&blacklist_type, &value).map_err(|e| e.to_string())
}

#[tauri::command]
fn get_blacklist(state: State<AppState>, blacklist_type: String) -> Result<Vec<String>, String> {
    let queue = state.queue.lock().map_err(|e| e.to_string())?;
    queue.get_blacklist(&blacklist_type).map_err(|e| e.to_string())
}

#[tauri::command]
fn is_first_run() -> bool {
    !std::path::Path::new("data/settings.json").exists()
}

#[tauri::command]
async fn check_updates() -> Result<(bool, String), String> {
    let current_version = "2.0.0";
    let url = "https://raw.githubusercontent.com/MalikHw/HwGDBot-db/main/ver.txt";
    
    log_info!("Checking for updates...");
    let response = reqwest::get(url).await.map_err(|e| e.to_string())?;
    let latest_version = response.text().await.map_err(|e| e.to_string())?;
    let latest_version = latest_version.trim();
    
    if latest_version != current_version {
        log_info!("New version available: {}", latest_version);
    }
    
    Ok((latest_version != current_version, latest_version.to_string()))
}

#[tauri::command]
async fn start_overlay(state: State<'_, AppState>) -> Result<(), String> {
    let queue = Arc::clone(&state.queue);
    let settings = Arc::clone(&state.settings);
    
    log_info!("Starting overlay server on port 6767");
    let server = overlay::OverlayServer::new(queue, settings);
    let handle = tokio::spawn(async move {
        if let Err(e) = server.start().await {
            log_error!("Overlay server error: {}", e);
        }
    });
    
    let mut overlay_handle = state.overlay_handle.lock().map_err(|e| e.to_string())?;
    *overlay_handle = Some(handle);
    
    Ok(())
}

#[tauri::command]
async fn stop_overlay(state: State<'_, AppState>) -> Result<(), String> {
    let mut handle = state.overlay_handle.lock().map_err(|e| e.to_string())?;
    if let Some(h) = handle.take() {
        h.abort();
        log_info!("Stopped overlay server");
    }
    Ok(())
}

#[tauri::command]
async fn create_backup() -> Result<String, String> {
    log_info!("Creating backup...");
    backup::BackupManager::create_backup()
}

#[tauri::command]
async fn restore_backup(backup_path: String) -> Result<(), String> {
    log_info!("Restoring backup from: {}", backup_path);
    backup::BackupManager::restore_backup(&backup_path)
}

#[tauri::command]
async fn list_backups() -> Result<Vec<String>, String> {
    backup::BackupManager::list_backups()
}

#[tauri::command]
fn open_backup_folder() -> Result<(), String> {
    let path = backup::BackupManager::get_backup_dir();
    std::fs::create_dir_all(&path).map_err(|e| e.to_string())?;
    
    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .arg(path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    
    Ok(())
}

#[tauri::command]
fn clear_cache() -> Result<(), String> {
    log_info!("Clearing cache...");
    std::fs::write("data/cache.json", "{}").map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn reset_played() -> Result<(), String> {
    log_info!("Resetting played list...");
    std::fs::write("data/played.json", "[]").map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn fetch_fucked_list() -> Result<(), String> {
    log_info!("Fetching fucked-out-list from GitHub...");
    let url = "https://raw.githubusercontent.com/MalikHw/HwGDBot-db/main/fucked-out-list.json";
    let response = reqwest::get(url).await.map_err(|e| e.to_string())?;
    let content = response.text().await.map_err(|e| e.to_string())?;
    std::fs::write("data/fucked-out-list.json", content).map_err(|e| e.to_string())?;
    log_info!("Fucked-out-list updated");
    Ok(())
}

fn create_tray() -> SystemTray {
    let copy_id = CustomMenuItem::new("copy_id".to_string(), "Copy Next Level ID");
    let show = CustomMenuItem::new("show".to_string(), "Show");
    let hide = CustomMenuItem::new("hide".to_string(), "Hide");
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");
    
    let tray_menu = SystemTrayMenu::new()
        .add_item(copy_id)
        .add_item(show)
        .add_item(hide)
        .add_item(quit);
    
    SystemTray::new().with_menu(tray_menu)
}

fn setup_panic_handler() {
    std::panic::set_hook(Box::new(|panic_info| {
        let msg = format!("PANIC: {:?}", panic_info);
        log_error!("{}", msg);
        
        // Create crash backup
        let timestamp = chrono::Local::now().format("%Y%m%d-%H%M%S");
        let backup_name = format!("data/queue_crash_backup_{}.json", timestamp);
        if let Ok(content) = std::fs::read_to_string("data/queue.json") {
            let _ = std::fs::write(&backup_name, content);
            log_info!("Created crash backup: {}", backup_name);
        }
        
        // Show error to user
        eprintln!("\n=== HwGDBot CRASHED ===");
        eprintln!("Please report log.txt to 'malikhw' on Discord");
        eprintln!("Crash backup saved to: {}", backup_name);
    }));
}

fn main() {
    setup_panic_handler();
    
    std::fs::create_dir_all("data").expect("Failed to create data directory");
    std::fs::create_dir_all("icons").ok();
    
    log_info!("=== HwGDBot Started ===");

    let mut queue = queue::Queue::load().unwrap_or_default();
    let settings = settings::Settings::load().unwrap_or_default();
    
    // Load queue from file if setting enabled
    if !settings.load_queue_on_start {
        queue = queue::Queue::default();
    }
    
    let queue_arc = Arc::new(Mutex::new(queue));
    let settings_arc = Arc::new(Mutex::new(settings.clone()));

    // Start auto backup if enabled
    if settings.backup_enabled {
        let interval = settings.backup_interval;
        tokio::spawn(async move {
            backup::start_auto_backup(interval as u64).await;
        });
    }
    
    // Fetch fucked-out-list on startup
    tokio::spawn(async {
        let _ = fetch_fucked_list().await;
    });

    tauri::Builder::default()
        .manage(AppState {
            queue: queue_arc,
            settings: settings_arc,
            twitch_handle: Mutex::new(None),
            youtube_handle: Mutex::new(None),
            overlay_handle: Mutex::new(None),
            sound_manager: Arc::new(sounds::SoundManager::new()),
            backup_handle: Mutex::new(None),
        })
        .system_tray(create_tray())
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::MenuItemClick { id, .. } => {
                match id.as_str() {
                    "copy_id" => {
                        if let Some(state) = app.try_state::<AppState>() {
                            if let Ok(queue) = state.queue.lock() {
                                if !queue.levels.is_empty() {
                                    let _ = arboard::Clipboard::new()
                                        .and_then(|mut cb| cb.set_text(&queue.levels[0].level_id));
                                }
                            }
                        }
                    }
                    "show" => {
                        if let Some(window) = app.get_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    "hide" => {
                        if let Some(window) = app.get_window("main") {
                            let _ = window.hide();
                        }
                    }
                    "quit" => {
                        log_info!("=== HwGDBot Shutdown ===");
                        std::process::exit(0);
                    }
                    _ => {}
                }
            }
            _ => {}
        })
        .invoke_handler(tauri::generate_handler![
            get_queue,
            remove_level,
            mark_played,
            copy_level_id,
            get_settings,
            save_settings,
            start_twitch,
            stop_twitch,
            start_youtube,
            stop_youtube,
            fetch_level,
            add_level_to_queue,
            add_to_blacklist,
            get_blacklist,
            is_first_run,
            check_updates,
            start_overlay,
            stop_overlay,
            create_backup,
            restore_backup,
            list_backups,
            open_backup_folder,
            clear_cache,
            reset_played,
            fetch_fucked_list,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
