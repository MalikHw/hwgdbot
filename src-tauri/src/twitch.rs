use irc::client::prelude::*;
use tauri::Window;

pub async fn start_twitch_bot(
    channel: String,
    token: String,
    post_cmd: String,
    del_cmd: String,
    window: Window,
) {
    let config = Config {
        nickname: Some(channel.clone()),
        server: Some("irc.chat.twitch.tv".to_string()),
        port: Some(6667),
        password: Some(format!("oauth:{}", token)),
        channels: vec![format!("#{}", channel)],
        ..Config::default()
    };

    let mut client = match Client::from_config(config).await {
        Ok(c) => c,
        Err(e) => {
            let _ = window.emit("twitch-error", format!("Failed to connect: {}", e));
            return;
        }
    };

    if let Err(e) = client.identify() {
        let _ = window.emit("twitch-error", format!("Failed to identify: {}", e));
        return;
    }

    let _ = window.emit("twitch-connected", "Connected to Twitch");

    let mut stream = client.stream().unwrap();

    while let Some(message) = stream.next().await.transpose().ok().flatten() {
        if let Command::PRIVMSG(_, msg) = message.command {
            let sender = message.source_nickname().unwrap_or("unknown").to_string();
            
            // Check for post command
            if msg.starts_with(&post_cmd) {
                let parts: Vec<&str> = msg.split_whitespace().collect();
                if parts.len() >= 2 {
                    let level_id = parts[1].to_string();
                    let _ = window.emit("level-requested", serde_json::json!({
                        "level_id": level_id,
                        "requester": sender,
                        "platform": "twitch"
                    }));
                }
            }
            
            // Check for delete command
            if msg.starts_with(&del_cmd) {
                let _ = window.emit("delete-requested", serde_json::json!({
                    "requester": sender,
                    "platform": "twitch"
                }));
            }
        }
    }
}

pub async fn send_ban(channel: String, token: String, username: String) -> Result<(), Box<dyn std::error::Error>> {
    let config = Config {
        nickname: Some(channel.clone()),
        server: Some("irc.chat.twitch.tv".to_string()),
        port: Some(6667),
        password: Some(format!("oauth:{}", token)),
        channels: vec![format!("#{}", channel)],
        ..Config::default()
    };

    let mut client = Client::from_config(config).await?;
    client.identify()?;
    
    client.send_privmsg(
        &format!("#{}", channel),
        &format!("/ban {}", username)
    )?;
    
    Ok(())
}