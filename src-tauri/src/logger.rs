use std::fs::{File, OpenOptions};
use std::io::Write;
use std::sync::Mutex;
use chrono::Local;

pub struct Logger {
    file: Mutex<File>,
}

impl Logger {
    pub fn new() -> Result<Self, std::io::Error> {
        let file = OpenOptions::new()
            .create(true)
            .append(true)
            .open("log.txt")?;
        
        Ok(Self {
            file: Mutex::new(file),
        })
    }
    
    pub fn log(&self, level: &str, message: &str) {
        let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S");
        let log_line = format!("[{}] [{}] {}\n", timestamp, level, message);
        
        if let Ok(mut file) = self.file.lock() {
            let _ = file.write_all(log_line.as_bytes());
            let _ = file.flush();
        }
        
        // Also print to console in debug mode
        #[cfg(debug_assertions)]
        print!("{}", log_line);
    }
    
    pub fn info(&self, message: &str) {
        self.log("INFO", message);
    }
    
    pub fn warn(&self, message: &str) {
        self.log("WARN", message);
    }
    
    pub fn error(&self, message: &str) {
        self.log("ERROR", message);
    }
    
    pub fn debug(&self, message: &str) {
        #[cfg(debug_assertions)]
        self.log("DEBUG", message);
    }
}

// Global logger instance
lazy_static::lazy_static! {
    pub static ref LOGGER: Logger = Logger::new().expect("Failed to create logger");
}

#[macro_export]
macro_rules! log_info {
    ($($arg:tt)*) => {
        $crate::logger::LOGGER.info(&format!($($arg)*))
    };
}

#[macro_export]
macro_rules! log_warn {
    ($($arg:tt)*) => {
        $crate::logger::LOGGER.warn(&format!($($arg)*))
    };
}

#[macro_export]
macro_rules! log_error {
    ($($arg:tt)*) => {
        $crate::logger::LOGGER.error(&format!($($arg)*))
    };
}

#[macro_export]
macro_rules! log_debug {
    ($($arg:tt)*) => {
        $crate::logger::LOGGER.debug(&format!($($arg)*))
    };
// }