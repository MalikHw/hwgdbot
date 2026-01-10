use std::sync::{Arc, Mutex};
use std::net::SocketAddr;
use tokio::net::TcpListener;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use crate::queue::Level;
use crate::settings::Settings;

pub struct OverlayServer {
    queue: Arc<Mutex<Vec<Level>>>,
    settings: Arc<Mutex<Settings>>,
}

impl OverlayServer {
    pub fn new(queue: Arc<Mutex<Vec<Level>>>, settings: Arc<Mutex<Settings>>) -> Self {
        Self { queue, settings }
    }
    
    pub async fn start(self) -> Result<(), Box<dyn std::error::Error>> {
        let addr = SocketAddr::from(([0, 0, 0, 0], 6767));
        let listener = TcpListener::bind(addr).await?;
        println!("Overlay server listening on http://localhost:6767");
        
        loop {
            let (mut socket, _) = listener.accept().await?;
            let queue = Arc::clone(&self.queue);
            let settings = Arc::clone(&self.settings);
            
            tokio::spawn(async move {
                let mut buffer = [0; 1024];
                if let Ok(_) = socket.read(&mut buffer).await {
                    let html = generate_overlay_html(&queue, &settings);
                    let response = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Length: {}\r\n\r\n{}",
                        html.len(),
                        html
                    );
                    let _ = socket.write_all(response.as_bytes()).await;
                }
            });
        }
    }
}

fn generate_overlay_html(queue: &Arc<Mutex<Vec<Level>>>, settings: &Arc<Mutex<Settings>>) -> String {
    let queue = queue.lock().unwrap();
    let settings = settings.lock().unwrap();
    
    let current_level = queue.first();
    let next_level = queue.get(1);
    
    let mut template = settings.overlay_template.clone();
    
    if let Some(level) = current_level {
        template = template
            .replace("{level}", &level.level_name)
            .replace("{author}", &level.author)
            .replace("{id}", &level.level_id)
            .replace("{difficulty}", &level.difficulty)
            .replace("{length}", &level.length)
            .replace("{requester}", &level.requester);
    } else {
        template = template
            .replace("{level}", "No level in queue")
            .replace("{author}", "-")
            .replace("{id}", "-")
            .replace("{difficulty}", "-")
            .replace("{length}", "-")
            .replace("{requester}", "-");
    }
    
    if let Some(next) = next_level {
        template = template
            .replace("{next-level}", &next.level_name)
            .replace("{next-author}", &next.author);
    } else {
        template = template
            .replace("{next-level}", "-")
            .replace("{next-author}", "-");
    }
    
    let font_face = if !settings.overlay_font.is_empty() {
        format!(
            r#"
            @font-face {{
                font-family: 'CustomFont';
                src: url('file://{}');
            }}
            "#,
            settings.overlay_font
        )
    } else {
        String::new()
    };
    
    let font_family = if !settings.overlay_font.is_empty() {
        "'CustomFont', sans-serif"
    } else {
        "Arial, sans-serif"
    };
    
    let transparency = settings.overlay_transparency as f32 / 100.0;
    
    format!(
        r#"<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">
    <style>
        {}
        body {{
            margin: 0;
            padding: 20px;
            font-family: {};
            color: {};
            background: rgba(0, 0, 0, {});
            font-size: 24px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            overflow: hidden;
        }}
        .overlay-content {{
            width: {}px;
            height: {}px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="overlay-content">{}</div>
</body>
</html>"#,
        font_face,
        font_family,
        settings.overlay_color,
        transparency,
        settings.overlay_width,
        settings.overlay_height,
        html_escape(&template)
    )
}

fn html_escape(text: &str) -> String {
    text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#39;")
}