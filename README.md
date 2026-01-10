# HwGDBot

<div align="center">

![HwGDBot Logo](icons/icon.png)

**The Ultimate Geometry Dash Level Request Bot for Streamers**

[![License](https://img.shields.io/badge/license-MPL_2.0-blue)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/MalikHw/HwGDBot/releases)
[![Discord](https://img.shields.io/badge/discord-@malikhw-7289da.svg)](https://discord.gg/5kn2uX5B8x)

[Page](https://malikhw.github.io/HwGDBot)

</div>

---

## ✨ Features

### 🎮 Multi-Platform Support
- **Twitch Integration** - Connect via IRC for real-time chat monitoring
- **YouTube Support** - Full livestream chat integration (requires Python)
- **Configurable Commands** - Customize !post and !del commands
- **Per-User Limits** - Set max submissions per user per stream

### 🛡️ Smart Auto Moderation
- **Crash/NSFW Database** - Automatically blocks known problematic levels
- **Duplicate Detection** - Prevents same level from being requested twice
- **Played History** - Optional filtering of already-played levels
- **Real-time Validation** - Fetches level data from GDBrowser API

### 🎯 Advanced Filters
- **Length Filters** - Tiny, Short, Medium, Long, XL
- **Difficulty Filters** - All difficulties including demon types
- **Rated/Unrated** - Filter by star rating status
- **Disliked Levels** - Block levels with negative rating
- **Large Levels** - Filter out 40k+ object levels

### 🚫 Powerful Blacklist System
- **Requester Blacklist** - Ban specific users from submitting
- **Creator Blacklist** - Block all levels from certain creators
- **Level ID Blacklist** - Ban specific level IDs
- **Easy Management** - One-click ban from queue

### 📺 OBS Overlay
- **Browser Source Ready** - Built-in HTTP server on port 6767
- **Customizable Template** - Use variables like {level}, {author}, {id}
- **Custom Fonts** - Load your own .ttf files
- **Adjustable Styling** - Change size, transparency, and colors
- **Auto-Refresh** - Updates every 5 seconds

### 🔔 Sound Notifications
- **New Level Sound** - Play when level is added to queue
- **Error Sound** - Play when level is rejected
- **Rate Limited** - Max once per 2 seconds to prevent spam
- **Multi-Format** - Supports .mp3, .ogg, .wav

### 💾 Backup & Recovery
- **Automatic Backups** - Scheduled backups (configurable interval)
- **Manual Backup** - Create backup anytime
- **Easy Restore** - One-click restore from .hgb-bkp files
- **Crash Recovery** - Auto-saves queue on crash
- **Keep Last 10** - Automatically manages backup history

### 🎨 Beautiful Interface
- **Material Design 3** - Modern, clean UI
- **Dark/Light Mode** - Follows OS theme
- **Blue Color Scheme** - Professional look
- **Difficulty Icons** - Visual indicators for each level
- **System Tray** - Minimize to tray, run in background

### 📊 Queue Management
- **Visual Queue** - See all requested levels at a glance
- **Level Details** - View full info for selected level
- **Quick Actions** - Copy ID, Skip, Mark Played, Report
- **Ban Controls** - Quick access to blacklist functions
- **Accept/Pause Toggle** - Stop accepting requests anytime

### 📝 Logging & Diagnostics
- **Comprehensive Logging** - Everything logged to log.txt
- **Crash Reports** - Automatic crash detection
- **Error Handling** - Graceful error recovery
- **Debug Info** - Helpful for troubleshooting

### 🔄 Update System
- **Auto-Check** - Checks for updates on startup
- **GitHub Integration** - Fetches latest version info
- **One-Click Download** - Opens download page automatically

### 💬 Report System
- **Report Levels** - Submit crash/NSFW levels to database
- **Twitch Ban Option** - Optionally ban requester on Twitch
- **Central Database** - Helps all HwGDBot users

---

## 🚀 Quick Start

### Windows
1. Download `HwGDBot-Windows.zip` from [releases](https://github.com/MalikHw/HwGDBot/releases/latest)
2. Extract and run `hwgdbot.exe`
3. Follow the setup wizard

### Linux
1. Download `HwGDBot-Linux.tar.gz` from [releases](https://github.com/MalikHw/HwGDBot/releases/latest)
2. Extract: `tar -xzf HwGDBot-Linux.tar.gz`
3. Run: `./HwGDBot-Linux/hwgdbot`

### YouTube Chat (Optional)
For YouTube support, install Python and pytchat:
```bash
pip install pytchat
```

**📖 Full setup instructions:** [QUICKSTART.md](QUICKSTART.md)

---

## 💻 Building from Source

### Prerequisites
- Rust (latest stable)
- Node.js 18+
- Python 3.8+ (for YouTube)
- Tauri CLI: `cargo install tauri-cli`

### Linux Dependencies
```bash
sudo apt-get install libwebkit2gtk-4.0-dev build-essential curl wget \
  libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
```

### Build
```bash
git clone https://github.com/MalikHw/HwGDBot.git
cd HwGDBot
cd src-tauri
cargo tauri build
```

**📖 Detailed build guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

## 🎮 Default Commands

Viewers use these commands in chat:
- `!post <level_id>` - Submit a level
- `!del` - Delete their last submission

*Commands are fully customizable in Settings → Commands*

---

## 🔧 Configuration

All settings accessible via the Settings dialog (⚙️ button):

### Connection Tab
- Twitch channel name & OAuth token
- YouTube livestream toggle

### Commands Tab
- Custom post/delete commands
- Max submissions per user

### Automod Tab
- Duplicate blocking
- Crash/NSFW filtering
- Played level filtering

### Filters Tab
- Length checkboxes
- Difficulty checkboxes
- Rated/Unrated dropdown
- Disliked & large level filters

### OBS Overlay Tab
- Enable/disable overlay
- Template customization
- Font, size, transparency, colors

### Sounds Tab
- Enable/disable sounds
- Select audio files

### Backup Tab
- Auto-backup toggle
- Interval settings
- Manual backup/restore

### Advanced Tab
- Queue save/load settings
- Cache management

---

## 🌐 Related Repositories

- **Main App**: [MalikHw/HwGDBot](https://github.com/MalikHw/HwGDBot)
- **Database**: [MalikHw/HwGDBot-db](https://github.com/MalikHw/HwGDBot-db) (fucked-out-list & version)
- **Website**: [malikhw.github.io/HwGDBot](https://malikhw.github.io/HwGDBot)
- **Donate**: [malikhw.github.io/donate](https://malikhw.github.io/donate)

---

**📖 More help:** [GitHub Issues](https://github.com/MalikHw/HwGDBot/issues)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

**Areas we'd love help with:**
- macOS support
- Translations
- Bug fixes
- Feature improvements
- Documentation

---

## 📞 Support

- **Discord**: @malikhw
- **GitHub Issues**: [Report bugs](https://github.com/MalikHw/HwGDBot/issues)
- **Email**: (help.malicorporation@gmail.com) (yes thats my mail 😭)

---

## ❤️ Support the Project

HwGDBot is **completely free** and always will be!

If you'd like to support development:
- ⭐ Star this repository
- ☕ [support me finanically](https://malikhw.github.io/donate)
- 📢 Share with other GD streamers
- 🐛 Report bugs and suggest features

---

## 📜 License

Mozilla Public License 2.0...

---

## 🎉 Credits

Made by **MalikHw** with ❤Love and some miku

Special thanks to:
- The Geometry Dash community
- GDColon (GDBrowser API)
- All contributors and users

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

<div align="center">

**Replacing LoquiBot, one stream at a time** 🚀

Made for streamers, by **a** streamer


</div>
