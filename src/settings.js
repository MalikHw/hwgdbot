const { invoke } = window.__TAURI__.tauri;
const { open: openDialog } = window.__TAURI__.dialog;

async function openSettings() {
    settings = await invoke('get_settings');
    document.getElementById('settings-dialog').style.display = 'flex';
    switchTab('connection');
}

function closeSettings() {
    document.getElementById('settings-dialog').style.display = 'none';
}

async function saveSettings() {
    try {
        // Gather all settings from form
        const newSettings = gatherSettings();
        await invoke('save_settings', { newSettings });
        settings = newSettings;
        alert('Settings saved successfully!');
        closeSettings();
    } catch (error) {
        alert('Failed to save settings: ' + error);
    }
}

function gatherSettings() {
    return {
        // Connection
        twitch_channel: getValue('twitch-channel'),
        twitch_token: getValue('twitch-token'),
        youtube_enabled: getChecked('youtube-enabled'),
        
        // Commands
        post_command: getValue('post-command'),
        delete_command: getValue('delete-command'),
        max_ids_per_user: parseInt(getValue('max-ids-per-user')) || 0,
        
        // Automod
        block_duplicate_from_same_user: getChecked('block-duplicate'),
        reject_crash_nsfw: getChecked('reject-crash-nsfw'),
        ignore_played: getChecked('ignore-played'),
        
        // Filters - Length
        length_tiny: getChecked('length-tiny'),
        length_short: getChecked('length-short'),
        length_medium: getChecked('length-medium'),
        length_long: getChecked('length-long'),
        length_xl: getChecked('length-xl'),
        
        // Filters - Difficulty
        diff_auto: getChecked('diff-auto'),
        diff_easy: getChecked('diff-easy'),
        diff_normal: getChecked('diff-normal'),
        diff_hard: getChecked('diff-hard'),
        diff_harder: getChecked('diff-harder'),
        diff_insane: getChecked('diff-insane'),
        diff_demon_easy: getChecked('diff-demon-easy'),
        diff_demon_medium: getChecked('diff-demon-medium'),
        diff_demon_hard: getChecked('diff-demon-hard'),
        diff_demon_insane: getChecked('diff-demon-insane'),
        diff_demon_extreme: getChecked('diff-demon-extreme'),
        
        // Filters - Other
        block_disliked: getChecked('block-disliked'),
        rated_filter: getValue('rated-filter'),
        block_large: getChecked('block-large'),
        
        // OBS Overlay
        overlay_enabled: getChecked('overlay-enabled'),
        overlay_template: getValue('overlay-template'),
        overlay_font: getValue('overlay-font'),
        overlay_width: parseInt(getValue('overlay-width')) || 800,
        overlay_height: parseInt(getValue('overlay-height')) || 100,
        overlay_transparency: parseInt(getValue('overlay-transparency')) || 0,
        overlay_color: getValue('overlay-color'),
        
        // Sounds
        sounds_enabled: getChecked('sounds-enabled'),
        sound_new_level: getValue('sound-new-level'),
        sound_error: getValue('sound-error'),
        
        // Backup
        backup_enabled: getChecked('backup-enabled'),
        backup_interval: parseInt(getValue('backup-interval')) || 10,
        
        // Advanced
        save_queue_on_change: getChecked('save-queue-on-change'),
        load_queue_on_start: getChecked('load-queue-on-start'),
        
        // UI
        show_donation_popup: settings.show_donation_popup,
    };
}

function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value : '';
}

function getChecked(id) {
    const el = document.getElementById(id);
    return el ? el.checked : false;
}

function switchTab(tabName) {
    // Update active tab
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.tab === tabName) {
            tab.classList.add('active');
        }
    });
    
    // Render tab content
    const content = document.getElementById('settings-content');
    content.innerHTML = renderTabContent(tabName);
}

// Setup tab listeners
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
});

function renderTabContent(tabName) {
    switch (tabName) {
        case 'connection':
            return `
                <div class="form-group">
                    <label>Twitch Channel Name</label>
                    <input type="text" id="twitch-channel" value="${settings.twitch_channel || ''}" placeholder="your_channel_name">
                </div>
                <div class="form-group">
                    <label>Twitch OAuth Token</label>
                    <input type="text" id="twitch-token" value="${settings.twitch_token || ''}" placeholder="oauth:your_token_here">
                    <p class="help-text">
                        Get your token from <a href="https://twitchtokengenerator.com" target="_blank">twitchtokengenerator.com</a><br>
                        Required scopes: <code>chat:read</code>, <code>chat:edit</code>, <code>channel:moderate</code>
                    </p>
                </div>
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="youtube-enabled" ${settings.youtube_enabled ? 'checked' : ''}>
                        <span>I'm a YouTube streamer</span>
                    </label>
                    <p class="help-text">Requires Python installed on your system</p>
                </div>
            `;
        
        case 'commands':
            return `
                <div class="form-group">
                    <label>Post Command</label>
                    <input type="text" id="post-command" value="${settings.post_command || '!post'}" placeholder="!post">
                    <p class="help-text">Command viewers use to submit levels (e.g., !post 12345678)</p>
                </div>
                <div class="form-group">
                    <label>Delete Command</label>
                    <input type="text" id="delete-command" value="${settings.delete_command || '!del'}" placeholder="!del">
                    <p class="help-text">Command viewers use to delete their last submission</p>
                </div>
                <div class="form-group">
                    <label>Max IDs per User per Stream</label>
                    <input type="number" id="max-ids-per-user" value="${settings.max_ids_per_user || 0}" min="0" placeholder="0">
                    <p class="help-text">0 = unlimited</p>
                </div>
            `;
        
        case 'automod':
            return `
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="block-duplicate" ${settings.block_duplicate_from_same_user ? 'checked' : ''}>
                        <span>Block same level from same user when requested twice</span>
                    </label>
                </div>
                <div class="form-group">
                    <label class="filter-checkbox" title="Always blocked - cannot be disabled">
                        <input type="checkbox" id="reject-crash-nsfw" checked disabled>
                        <span>Reject crash/NSFW levels from database (always blocked)</span>
                    </label>
                </div>
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="ignore-played" ${settings.ignore_played ? 'checked' : ''}>
                        <span>Ignore already-played levels</span>
                    </label>
                </div>
            `;
        
        case 'filters':
            return `
                <h3>Length Filters</h3>
                <div class="filters-grid">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="length-tiny" ${settings.length_tiny ? 'checked' : ''}>
                        <span>Tiny</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="length-short" ${settings.length_short ? 'checked' : ''}>
                        <span>Short</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="length-medium" ${settings.length_medium ? 'checked' : ''}>
                        <span>Medium</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="length-long" ${settings.length_long ? 'checked' : ''}>
                        <span>Long</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="length-xl" ${settings.length_xl ? 'checked' : ''}>
                        <span>XL</span>
                    </label>
                </div>
                
                <h3 style="margin-top: 24px;">Difficulty Filters</h3>
                <div class="filters-grid">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-auto" ${settings.diff_auto ? 'checked' : ''}>
                        <span>Auto</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-easy" ${settings.diff_easy ? 'checked' : ''}>
                        <span>Easy</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-normal" ${settings.diff_normal ? 'checked' : ''}>
                        <span>Normal</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-hard" ${settings.diff_hard ? 'checked' : ''}>
                        <span>Hard</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-harder" ${settings.diff_harder ? 'checked' : ''}>
                        <span>Harder</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-insane" ${settings.diff_insane ? 'checked' : ''}>
                        <span>Insane</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-demon-easy" ${settings.diff_demon_easy ? 'checked' : ''}>
                        <span>Easy Demon</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-demon-medium" ${settings.diff_demon_medium ? 'checked' : ''}>
                        <span>Medium Demon</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-demon-hard" ${settings.diff_demon_hard ? 'checked' : ''}>
                        <span>Hard Demon</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-demon-insane" ${settings.diff_demon_insane ? 'checked' : ''}>
                        <span>Insane Demon</span>
                    </label>
                    <label class="filter-checkbox">
                        <input type="checkbox" id="diff-demon-extreme" ${settings.diff_demon_extreme ? 'checked' : ''}>
                        <span>Extreme Demon</span>
                    </label>
                </div>
                
                <h3 style="margin-top: 24px;">Other Filters</h3>
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="block-disliked" ${settings.block_disliked ? 'checked' : ''}>
                        <span>Block disliked levels</span>
                    </label>
                </div>
                <div class="form-group">
                    <label>Rated Filter</label>
                    <select id="rated-filter">
                        <option value="any" ${settings.rated_filter === 'any' ? 'selected' : ''}>Any</option>
                        <option value="rated" ${settings.rated_filter === 'rated' ? 'selected' : ''}>Rated Only</option>
                        <option value="unrated" ${settings.rated_filter === 'unrated' ? 'selected' : ''}>Unrated Only</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="block-large" ${settings.block_large ? 'checked' : ''}>
                        <span>Block large levels (40k+ objects)</span>
                    </label>
                </div>
            `;
        
        case 'overlay':
            return `
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="overlay-enabled" ${settings.overlay_enabled ? 'checked' : ''}>
                        <span>Enable OBS Overlay</span>
                    </label>
                    <p class="help-text">Starts a local server for browser source overlay</p>
                </div>
                <div class="form-group">
                    <label>Template Text</label>
                    <textarea id="overlay-template" rows="3">${settings.overlay_template || ''}</textarea>
                    <p class="help-text">Available variables: {level}, {author}, {id}, {next-level}, {next-author}, {difficulty}, {length}</p>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Width (px)</label>
                        <input type="number" id="overlay-width" value="${settings.overlay_width || 800}" min="100">
                    </div>
                    <div class="form-group">
                        <label>Height (px)</label>
                        <input type="number" id="overlay-height" value="${settings.overlay_height || 100}" min="50">
                    </div>
                </div>
                <div class="form-group">
                    <label>Transparency (0-100%)</label>
                    <input type="number" id="overlay-transparency" value="${settings.overlay_transparency || 0}" min="0" max="100">
                </div>
                <div class="form-group">
                    <label>Text Color</label>
                    <input type="text" id="overlay-color" value="${settings.overlay_color || '#FFFFFF'}" placeholder="#FFFFFF">
                </div>
                <div class="form-group">
                    <label>Custom Font (.ttf)</label>
                    <input type="text" id="overlay-font" value="${settings.overlay_font || ''}" placeholder="Path to .ttf file">
                    <button class="btn" onclick="selectOverlayFont()">Browse...</button>
                </div>
                <p class="help-text">Overlay URL: http://localhost:6767</p>
            `;
        
        case 'sounds':
            return `
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="sounds-enabled" ${settings.sounds_enabled ? 'checked' : ''}>
                        <span>Enable Sounds</span>
                    </label>
                </div>
                <div class="form-group">
                    <label>New Level Sound</label>
                    <input type="text" id="sound-new-level" value="${settings.sound_new_level || ''}" placeholder="Path to audio file">
                    <button class="btn" onclick="selectNewLevelSound()">Browse...</button>
                </div>
                <div class="form-group">
                    <label>Error/Blocked Sound</label>
                    <input type="text" id="sound-error" value="${settings.sound_error || ''}" placeholder="Path to audio file">
                    <button class="btn" onclick="selectErrorSound()">Browse...</button>
                </div>
                <p class="help-text">Supports .mp3, .ogg, .wav files</p>
            `;
        
        case 'backup':
            return `
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="backup-enabled" ${settings.backup_enabled ? 'checked' : ''}>
                        <span>Enable Automatic Backup</span>
                    </label>
                </div>
                <div class="form-group">
                    <label>Backup Interval (minutes)</label>
                    <input type="number" id="backup-interval" value="${settings.backup_interval || 10}" min="1" max="120">
                    <p class="help-text">Backups are saved to Documents/HwGDBot/</p>
                </div>
                <div style="display: flex; gap: 8px; flex-direction: column;">
                    <button class="btn btn-primary" onclick="backupNow()">Backup Now</button>
                    <button class="btn" onclick="restoreBackup()">Restore from Backup</button>
                    <button class="btn" onclick="openBackupFolder()">Open Backup Folder</button>
                </div>
            `;
        
        case 'advanced':
            return `
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="save-queue-on-change" ${settings.save_queue_on_change ? 'checked' : ''}>
                        <span>Save queue on every change</span>
                    </label>
                </div>
                <div class="form-group">
                    <label class="filter-checkbox">
                        <input type="checkbox" id="load-queue-on-start" ${settings.load_queue_on_start ? 'checked' : ''}>
                        <span>Load queue on app start</span>
                    </label>
                </div>
                <div style="display: flex; gap: 8px; flex-direction: column; margin-top: 24px;">
                    <button class="btn btn-warning" onclick="clearCache()">Clear Cache</button>
                    <button class="btn btn-warning" onclick="resetPlayed()">Reset Played List</button>
                </div>
            `;
        
        default:
            return '<p>Unknown tab</p>';
    }
}

async function selectOverlayFont() {
    const selected = await openDialog({
        filters: [{ name: 'Font Files', extensions: ['ttf'] }]
    });
    if (selected) {
        document.getElementById('overlay-font').value = selected;
    }
}

async function selectNewLevelSound() {
    const selected = await openDialog({
        filters: [{ name: 'Audio Files', extensions: ['mp3', 'ogg', 'wav'] }]
    });
    if (selected) {
        document.getElementById('sound-new-level').value = selected;
    }
}

async function selectErrorSound() {
    const selected = await openDialog({
        filters: [{ name: 'Audio Files', extensions: ['mp3', 'ogg', 'wav'] }]
    });
    if (selected) {
        document.getElementById('sound-error').value = selected;
    }
}

async function backupNow() {
    try {
        const path = await invoke('create_backup');
        alert(`Backup created successfully!\nSaved to: ${path}`);
    } catch (error) {
        alert('Failed to create backup: ' + error);
    }
}

async function restoreBackup() {
    const { open: openDialog } = window.__TAURI__.dialog;
    try {
        const selected = await openDialog({
            filters: [{ name: 'HwGDBot Backup', extensions: ['hgb-bkp'] }]
        });
        
        if (selected) {
            if (confirm('This will replace all current data. Continue?')) {
                await invoke('restore_backup', { backupPath: selected });
                alert('Backup restored! Please restart the app.');
            }
        }
    } catch (error) {
        alert('Failed to restore backup: ' + error);
    }
}

async function openBackupFolder() {
    try {
        await invoke('open_backup_folder');
    } catch (error) {
        alert('Failed to open backup folder: ' + error);
    }
}

async function clearCache() {
    if (confirm('Clear all cached GD data?')) {
        try {
            await invoke('clear_cache');
            alert('Cache cleared successfully!');
        } catch (error) {
            alert('Failed to clear cache: ' + error);
        }
    }
}

async function resetPlayed() {
    if (confirm('Reset played levels list?')) {
        try {
            await invoke('reset_played');
            alert('Played list reset successfully!');
        } catch (error) {
            alert('Failed to reset played list: ' + error);
        }
    }
}