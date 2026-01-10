use std::process::{Command, Child, Stdio};
use std::io::{BufRead, BufReader};
use tauri::Window;
use std::thread;

pub fn start_youtube_bot(
    video_id: String,
    post_cmd: String,
    del_cmd: String,
    window: Window,
) -> Result<Child, std::io::Error> {
    // Check if Python is installed
    let python_check = Command::new("python")
        .arg("--version")
        .output();
    
    let python_cmd = if python_check.is_ok() {
        "python"
    } else {
        let python3_check = Command::new("python3")
            .arg("--version")
            .output();
        if python3_check.is_ok() {
            "python3"
        } else {
            return Err(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "Python not found. Please install Python to use YouTube chat."
            ));
        }
    };
    
    let mut child = Command::new(python_cmd)
        .arg("python/youtube-chat-fehtch.py")
        .arg(&video_id)
        .arg(&post_cmd)
        .arg(&del_cmd)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;
    
    if let Some(stdout) = child.stdout.take() {
        let reader = BufReader::new(stdout);
        let window_clone = window.clone();
        
        thread::spawn(move || {
            for line in reader.lines().filter_map(|l| l.ok()) {
                if line.starts_with("LEVEL:") {
                    let parts: Vec<&str> = line.strip_prefix("LEVEL:").unwrap().split('|').collect();
                    if parts.len() >= 2 {
                        let _ = window_clone.emit("level-requested", serde_json::json!({
                            "level_id": parts[0],
                            "requester": parts[1],
                            "platform": "youtube"
                        }));
                    }
                } else if line.starts_with("DELETE:") {
                    let requester = line.strip_prefix("DELETE:").unwrap();
                    let _ = window_clone.emit("delete-requested", serde_json::json!({
                        "requester": requester,
                        "platform": "youtube"
                    }));
                } else if line.starts_with("ERROR:") {
                    let _ = window_clone.emit("youtube-error", line.strip_prefix("ERROR:").unwrap());
                } else if line.starts_with("CONNECTED") {
                    let _ = window_clone.emit("youtube-connected", "Connected to YouTube");
                }
            }
        });
    }
    
    Ok(child)
}