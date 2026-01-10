const { invoke } = window.__TAURI__.tauri;
const { listen } = window.__TAURI__.event;
const { writeText } = window.__TAURI__.clipboard;
const { open: openUrl } = window.__TAURI__.shell;

let currentQueue = [];
let selectedIndex = -1;
let settings = {};

// Initialize app
window.addEventListener('DOMContentLoaded', async () => {
    // Show splash for 500ms
    setTimeout(async () => {
        document.getElementById('splash-screen').style.display = 'none';
        
        // Check if first run
        const isFirst = await invoke('is_first_run');
        if (isFirst) {
            document.getElementById('first-run-dialog').style.display = 'flex';
        } else {
            await initApp();
        }
    }, 500);
});

function showFirstRunStep2() {
    document.getElementById('first-run-step-1').style.display = 'none';
    document.getElementById('first-run-step-2').style.display = 'block';
}

async function finishFirstRun() {
    document.getElementById('first-run-dialog').style.display = 'none';
    await initApp();
    
    // Animate settings button
    const settingsBtn = document.getElementById('settings-btn');
    settingsBtn.classList.add('animate-settings');
    setTimeout(() => {
        settingsBtn.classList.remove('animate-settings');
    }, 1500);
}

async function initApp() {
    document.getElementById('main-window').style.display = 'flex';
    
    // Load settings
    settings = await invoke('get_settings');
    
    // Show donation popup if enabled
    if (settings.show_donation_popup) {
        document.getElementById('donation-dialog').style.display = 'flex';
    }
    
    // Load queue
    await refreshQueue();
    
    // Setup event listeners
    setupEventListeners();
    
    // Check for updates
    checkUpdates();
    
    // Start overlay if enabled
    if (settings.overlay_enabled) {
        try {
            await invoke('start_overlay');
            console.log('Overlay server started on http://localhost:6767');
        } catch (error) {
            console.error('Failed to start overlay:', error);
        }
    }
    
    // Fetch fucked-out-list
    try {
        await invoke('fetch_fucked_list');
    } catch (error) {
        console.error('Failed to fetch fucked-out-list:', error);
    }
}

function setupEventListeners() {
    // Listen for level requests from Twitch/YouTube
    listen('level-requested', async (event) => {
        const { level_id, requester, platform } = event.payload;
        await handleLevelRequest(level_id, requester, platform);
    });
    
    listen('delete-requested', async (event) => {
        const { requester, platform } = event.payload;
        await handleDeleteRequest(requester, platform);
    });
    
    listen('twitch-connected', () => {
        updateStatus('twitch', 'connected');
    });
    
    listen('twitch-error', (event) => {
        updateStatus('twitch', 'error');
        alert('Twitch Error: ' + event.payload);
    });
    
    listen('youtube-connected', () => {
        updateStatus('youtube', 'connected');
    });
    
    listen('youtube-error', (event) => {
        updateStatus('youtube', 'error');
        alert('YouTube Error: ' + event.payload);
    });
    
    // Accept requests toggle
    document.getElementById('accept-requests').addEventListener('change', (e) => {
        if (e.target.checked) {
            startConnections();
        } else {
            stopConnections();
        }
    });
    
    // Settings button
    document.getElementById('settings-btn').addEventListener('click', openSettings);
    
    // Start connections if configured
    if (settings.twitch_channel && settings.twitch_token) {
        document.getElementById('accept-requests').checked = true;
        startConnections();
    }
}

async function handleLevelRequest(level_id, requester, platform) {
    if (!document.getElementById('accept-requests').checked) {
        return;
    }
    
    try {
        // Fetch level data
        const gdLevel = await invoke('fetch_level', { levelId: level_id });
        
        // Create level object
        const level = {
            level_id: gdLevel.id,
            level_name: gdLevel.name,
            author: gdLevel.author,
            song: gdLevel.song,
            difficulty: gdLevel.difficulty,
            difficulty_face: gdLevel.difficulty_face,
            length: gdLevel.length,
            requester: requester,
            platform: platform,
            timestamp: Date.now(),
            attempts: 0,
            is_rated: gdLevel.is_rated,
            is_disliked: gdLevel.is_disliked,
            is_large: gdLevel.is_large,
        };
        
        // Add to queue
        await invoke('add_level_to_queue', { level });
        await refreshQueue();
        
        // Play sound if enabled
        if (settings.sounds_enabled && settings.sound_new_level) {
            playSound(settings.sound_new_level);
        }
    } catch (error) {
        console.error('Error adding level:', error);
        if (settings.sounds_enabled && settings.sound_error) {
            playSound(settings.sound_error);
        }
    }
}

async function handleDeleteRequest(requester, platform) {
    // Find last level from this requester
    for (let i = currentQueue.length - 1; i >= 0; i--) {
        if (currentQueue[i].requester === requester && currentQueue[i].platform === platform) {
            await invoke('remove_level', { index: i });
            await refreshQueue();
            break;
        }
    }
}

async function refreshQueue() {
    currentQueue = await invoke('get_queue');
    renderQueue();
    document.getElementById('queue-count').textContent = currentQueue.length;
}

function renderQueue() {
    const queueList = document.getElementById('queue-list');
    
    if (currentQueue.length === 0) {
        queueList.innerHTML = '<p class="empty-state">Queue is empty</p>';
        clearSelection();
        return;
    }
    
    queueList.innerHTML = currentQueue.map((level, index) => {
        const diffIcon = `icons/${level.difficulty_face}.png`;
        const ratedBadge = level.is_rated ? '⭐' : '';
        const largeBadge = level.is_large ? '(+)' : '';
        
        return `
            <div class="queue-item ${index === selectedIndex ? 'selected' : ''}" onclick="selectLevel(${index})">
                <div class="queue-item-header">
                    <img src="${diffIcon}" class="difficulty-icon" onerror="this.style.display='none'">
                    <span class="level-name">${level.level_name} ${ratedBadge} ${largeBadge}</span>
                </div>
                <div class="queue-item-meta">
                    ${level.author} • ${level.requester} (${level.platform})
                </div>
            </div>
        `;
    }).join('');
}

function selectLevel(index) {
    selectedIndex = index;
    renderQueue();
    displayLevelInfo(currentQueue[index]);
    enableButtons();
}

function displayLevelInfo(level) {
    const info = document.getElementById('level-info');
    info.innerHTML = `
        <div class="info-row"><span>Level ID:</span><strong>${level.level_id}</strong></div>
        <div class="info-row"><span>Name:</span><strong>${level.level_name}</strong></div>
        <div class="info-row"><span>Author:</span><strong>${level.author}</strong></div>
        <div class="info-row"><span>Song:</span><strong>${level.song}</strong></div>
        <div class="info-row"><span>Difficulty:</span><strong>${level.difficulty}</strong></div>
        <div class="info-row"><span>Length:</span><strong>${level.length}</strong></div>
        <div class="info-row"><span>Rated:</span><strong>${level.is_rated ? 'Yes ⭐' : 'No'}</strong></div>
        <div class="info-row"><span>Large:</span><strong>${level.is_large ? 'Yes (+)' : 'No'}</strong></div>
        <div class="info-row"><span>Requester:</span><strong>${level.requester} (${level.platform})</strong></div>
    `;
}

function clearSelection() {
    selectedIndex = -1;
    document.getElementById('level-info').innerHTML = '<p class="empty-state">Select a level from the queue</p>';
    disableButtons();
}

function enableButtons() {
    document.getElementById('copy-btn').disabled = false;
    document.getElementById('skip-btn').disabled = false;
    document.getElementById('played-btn').disabled = false;
    document.getElementById('report-btn').disabled = false;
    document.getElementById('ban-requester-btn').disabled = false;
    document.getElementById('ban-creator-btn').disabled = false;
    document.getElementById('ban-id-btn').disabled = false;
}

function disableButtons() {
    document.getElementById('copy-btn').disabled = true;
    document.getElementById('skip-btn').disabled = true;
    document.getElementById('played-btn').disabled = true;
    document.getElementById('report-btn').disabled = true;
    document.getElementById('ban-requester-btn').disabled = true;
    document.getElementById('ban-creator-btn').disabled = true;
    document.getElementById('ban-id-btn').disabled = true;
}

async function copyLevelId() {
    if (selectedIndex >= 0) {
        const levelId = currentQueue[selectedIndex].level_id;
        await writeText(levelId);
    }
}

async function skipLevel() {
    if (selectedIndex >= 0) {
        await invoke('remove_level', { index: selectedIndex });
        await refreshQueue();
    }
}

async function markPlayed() {
    if (selectedIndex >= 0) {
        await invoke('mark_played', { index: selectedIndex });
        await refreshQueue();
    }
}

function reportLevel() {
    if (selectedIndex >= 0) {
        const level = currentQueue[selectedIndex];
        document.getElementById('report-level-info').innerHTML = `
            <div class="info-row"><span>Level:</span><strong>${level.level_name}</strong></div>
            <div class="info-row"><span>Author:</span><strong>${level.author}</strong></div>
            <div class="info-row"><span>ID:</span><strong>${level.level_id}</strong></div>
        `;
        
        // Show ban option for Twitch
        if (level.platform === 'twitch') {
            document.getElementById('report-ban-option').style.display = 'block';
            document.getElementById('report-ban-text').textContent = `Ban ${level.requester} from my Twitch channel`;
        } else {
            document.getElementById('report-ban-option').style.display = 'none';
        }
        
        document.getElementById('report-dialog').style.display = 'flex';
    }
}

async function submitReport() {
    const reason = document.getElementById('report-reason').value.trim();
    if (!reason) {
        alert('Please provide a reason for the report');
        return;
    }
    
    const level = currentQueue[selectedIndex];
    const banChecked = document.getElementById('report-ban-twitch').checked;
    
    try {
        // Submit report to server
        const response = await fetch('https://hwgdbot.rf.gd/fuckit.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                level_id: level.level_id,
                level_name: level.level_name,
                author: level.author,
                reason: reason,
                reporter: 'anonymous'
            })
        });
        
        if (response.ok) {
            alert('Report submitted successfully');
            
            // Ban on Twitch if checked
            if (banChecked && level.platform === 'twitch') {
                // This would need to be implemented in Rust
                alert('Ban feature coming soon');
            }
            
            closeReportDialog();
        } else {
            alert('Failed to submit report');
        }
    } catch (error) {
        alert('Error submitting report: ' + error);
    }
}

function closeReportDialog() {
    document.getElementById('report-dialog').style.display = 'none';
    document.getElementById('report-reason').value = '';
    document.getElementById('report-ban-twitch').checked = false;
}

async function banRequester() {
    if (selectedIndex >= 0) {
        const level = currentQueue[selectedIndex];
        if (confirm(`Ban requester "${level.requester}"?`)) {
            await invoke('add_to_blacklist', { blacklistType: 'requesters', value: level.requester });
            await invoke('remove_level', { index: selectedIndex });
            await refreshQueue();
        }
    }
}

async function banCreator() {
    if (selectedIndex >= 0) {
        const level = currentQueue[selectedIndex];
        if (confirm(`Ban creator "${level.author}"?`)) {
            await invoke('add_to_blacklist', { blacklistType: 'creators', value: level.author });
            await invoke('remove_level', { index: selectedIndex });
            await refreshQueue();
        }
    }
}

async function banLevelId() {
    if (selectedIndex >= 0) {
        const level = currentQueue[selectedIndex];
        if (confirm(`Ban level ID "${level.level_id}"?`)) {
            await invoke('add_to_blacklist', { blacklistType: 'ids', value: level.level_id });
            await invoke('remove_level', { index: selectedIndex });
            await refreshQueue();
        }
    }
}

function updateStatus(platform, status) {
    const statusEl = document.getElementById(`${platform}-status`);
    const icons = { disconnected: '⚪', connected: '🟢', error: '🔴' };
    const text = platform.charAt(0).toUpperCase() + platform.slice(1);
    statusEl.textContent = `${icons[status]} ${text}`;
}

async function startConnections() {
    if (settings.twitch_channel && settings.twitch_token) {
        try {
            await invoke('start_twitch');
        } catch (error) {
            console.error('Failed to start Twitch:', error);
        }
    }
    
    if (settings.youtube_enabled) {
        const videoId = prompt('Enter YouTube livestream URL or ID:');
        if (videoId) {
            const id = extractYouTubeId(videoId);
            if (id) {
                try {
                    await invoke('start_youtube', { videoId: id });
                } catch (error) {
                    alert('Failed to connect to YouTube: ' + error);
                }
            } else {
                alert('Invalid YouTube URL or ID');
            }
        }
    }
}

async function stopConnections() {
    await invoke('stop_twitch');
    await invoke('stop_youtube');
    updateStatus('twitch', 'disconnected');
    updateStatus('youtube', 'disconnected');
}

function extractYouTubeId(url) {
    const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/,
        /^([a-zA-Z0-9_-]{11})$/
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }
    return null;
}

function playSound(file) {
    // Simple sound playback
    const audio = new Audio(file);
    audio.play().catch(() => {});
}

function openDonation() {
    openUrl('https://malikhw.github.io/donate');
}

function closeDonation() {
    const dontShow = document.getElementById('dont-show-donation').checked;
    if (dontShow) {
        settings.show_donation_popup = false;
        invoke('save_settings', { newSettings: settings });
    }
    document.getElementById('donation-dialog').style.display = 'none';
}

async function checkUpdates() {
    try {
        const [hasUpdate, latestVersion] = await invoke('check_updates');
        if (hasUpdate) {
            if (confirm(`New version ${latestVersion} available! Download now?`)) {
                openUrl('https://malikhw.github.io/HwGDBot');
            }
        }
    } catch (error) {
        console.error('Update check failed:', error);
    }
}