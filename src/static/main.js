// ===== CONSTANTS =====
const SWIPE_THRESHOLD = 50;
const VERTICAL_THRESHOLD = 100;
const API_TIMEOUT = 10000;

// ===== APP STATE =====
const AppState = {
    stories: [],
    currentStoryIndex: 0,
    currentStory: null,
    isPlaying: false,
    isLoading: false,
    error: null,
    playbackStartTime: null,
    lastPlaybackTime: 0
};

// ===== DOM ELEMENTS =====
const DOM = {
    audioPlayer: document.getElementById('audioPlayer'),
    playButton: document.getElementById('playButton'),
    progressBar: document.getElementById('progressBar'),
    progressContainer: document.getElementById('progressContainer'),
    currentTimeDisplay: document.getElementById('currentTime'),
    durationDisplay: document.getElementById('duration'),
    coverImage: document.getElementById('coverImage'),
    storyTitle: document.getElementById('storyTitle'),
    storySummary: document.getElementById('storySummary'),
    storySlider: document.getElementById('storySlider'),
    menuButton: document.getElementById('menuButton'),
    menu: document.getElementById('menu'),
    swipeEdgeLeft: document.getElementById('swipeEdgeLeft'),
    swipeEdgeRight: document.getElementById('swipeEdgeRight'),
    container: document.getElementById('container')
};

// ===== UTILITY FUNCTIONS =====
function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function showLoading() {
    if (!AppState.isLoading) {
        AppState.isLoading = true;
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.id = 'loadingSpinner';
        document.body.appendChild(spinner);
    }
}

function hideLoading() {
    AppState.isLoading = false;
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.remove();
    }
}

function showError(title, message) {
    AppState.error = { title, message };
    hideLoading();

    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <h2>${title}</h2>
        <p>${message}</p>
    `;
    errorDiv.id = 'errorMessage';
    document.body.appendChild(errorDiv);

    setTimeout(() => {
        errorDiv.remove();
        AppState.error = null;
    }, 5000);
}

async function trackPlaytime(storyId, duration) {
    try {
        await fetch('/api/playtime', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ story_id: storyId, play_duration: Math.floor(duration) })
        });
    } catch (error) {
        console.error('Failed to track playtime:', error);
    }
}

function updateMenuState(isOpen) {
    DOM.menu.classList.toggle('active', isOpen);
    DOM.menuButton.classList.toggle('active', isOpen);
    DOM.menuButton.setAttribute('aria-expanded', isOpen.toString());
    DOM.menuButton.setAttribute('aria-label', isOpen ? 'Menü schließen' : 'Menü öffnen');
}

// ===== MENU HANDLING =====
if (DOM.menuButton && DOM.menu) {
    DOM.menuButton.addEventListener('click', () => {
        const isOpen = !DOM.menu.classList.contains('active');
        updateMenuState(isOpen);
    });

    DOM.menu.addEventListener('click', (e) => {
        if (e.target === DOM.menu || e.target.tagName === 'A') {
            updateMenuState(false);
        }
    });

    // Close menu on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && DOM.menu.classList.contains('active')) {
            updateMenuState(false);
        }
    });
}

// ===== STORY LOADING =====
async function loadStories() {
    if (!DOM.storyTitle) return; // Skip if not on index page

    try {
        showLoading();

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

        const response = await fetch('/api/stories', {
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.stories || data.stories.length === 0) {
            throw new Error('Keine Stories verfügbar');
        }

        AppState.stories = data.stories;
        AppState.currentStoryIndex = Math.floor(Math.random() * AppState.stories.length);

        hideLoading();
        loadStory(AppState.stories[AppState.currentStoryIndex]);

    } catch (error) {
        hideLoading();

        if (error.name === 'AbortError') {
            showError('Zeitüberschreitung', 'Laden dauert zu lange. Bitte versuche es erneut.');
        } else {
            console.error('Error loading stories:', error);
            showError('Fehler beim Laden', 'Bitte Seite neu laden oder später versuchen.');
        }

        if (DOM.storyTitle) DOM.storyTitle.textContent = 'Keine Stories verfügbar';
        if (DOM.storySummary) DOM.storySummary.textContent = '';
    }
}

function loadStory(story) {
    if (!story) return;

    AppState.currentStory = story;

    // Update UI
    if (DOM.coverImage) {
        DOM.coverImage.style.backgroundImage = `url('${story.cover_url}')`;
    }
    if (DOM.storyTitle) {
        DOM.storyTitle.textContent = story.title;
    }
    if (DOM.storySummary) {
        DOM.storySummary.textContent = story.summary;
    }

    // Update audio
    if (DOM.audioPlayer) {
        DOM.audioPlayer.src = story.audio_url;
        DOM.audioPlayer.load();
    }

    // Reset player state
    if (AppState.isPlaying) {
        AppState.isPlaying = false;
        DOM.playButton?.classList.remove('playing');
        DOM.playButton?.setAttribute('aria-pressed', 'false');
        DOM.playButton?.setAttribute('aria-label', 'Abspielen');
    }

    if (DOM.progressBar) {
        DOM.progressBar.style.width = '0%';
    }
    if (DOM.progressContainer) {
        DOM.progressContainer.setAttribute('aria-valuenow', '0');
    }
    if (DOM.currentTimeDisplay) {
        DOM.currentTimeDisplay.textContent = '00:00';
    }
}

// ===== AUDIO PLAYER CONTROLS =====
function togglePlay() {
    if (!AppState.currentStory || !DOM.audioPlayer) return;

    if (AppState.isPlaying) {
        DOM.audioPlayer.pause();
    } else {
        const playPromise = DOM.audioPlayer.play();
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.error('Playback error:', error);
                showError('Wiedergabefehler', 'Audio konnte nicht abgespielt werden.');
            });
        }
    }
}

function updatePlayButtonState(playing) {
    AppState.isPlaying = playing;
    DOM.playButton?.classList.toggle('playing', playing);
    DOM.playButton?.setAttribute('aria-pressed', playing.toString());
    DOM.playButton?.setAttribute('aria-label', playing ? 'Pausieren' : 'Abspielen');
}

if (DOM.playButton) {
    DOM.playButton.addEventListener('click', togglePlay);
}

if (DOM.audioPlayer) {
    DOM.audioPlayer.addEventListener('play', () => {
        updatePlayButtonState(true);
        AppState.playbackStartTime = Date.now();
        AppState.lastPlaybackTime = DOM.audioPlayer.currentTime;
    });

    DOM.audioPlayer.addEventListener('pause', () => {
        updatePlayButtonState(false);
        if (AppState.playbackStartTime && AppState.currentStory) {
            const duration = (Date.now() - AppState.playbackStartTime) / 1000;
            trackPlaytime(AppState.currentStory.id, duration);
            AppState.playbackStartTime = null;
        }
    });

    DOM.audioPlayer.addEventListener('ended', () => {
        updatePlayButtonState(false);
        if (AppState.playbackStartTime && AppState.currentStory) {
            const duration = (Date.now() - AppState.playbackStartTime) / 1000;
            trackPlaytime(AppState.currentStory.id, duration);
            AppState.playbackStartTime = null;
        }
        if (DOM.progressBar) DOM.progressBar.style.width = '0%';
        if (DOM.progressContainer) DOM.progressContainer.setAttribute('aria-valuenow', '0');
    });

    DOM.audioPlayer.addEventListener('loadedmetadata', () => {
        if (DOM.durationDisplay) {
            DOM.durationDisplay.textContent = formatTime(DOM.audioPlayer.duration);
        }
        if (DOM.progressContainer) {
            DOM.progressContainer.setAttribute('aria-valuemax', Math.floor(DOM.audioPlayer.duration).toString());
        }
    });

    DOM.audioPlayer.addEventListener('timeupdate', () => {
        if (DOM.audioPlayer.duration) {
            const progress = (DOM.audioPlayer.currentTime / DOM.audioPlayer.duration) * 100;

            if (DOM.progressBar) {
                DOM.progressBar.style.width = `${progress}%`;
            }
            if (DOM.currentTimeDisplay) {
                DOM.currentTimeDisplay.textContent = formatTime(DOM.audioPlayer.currentTime);
            }
            if (DOM.progressContainer) {
                DOM.progressContainer.setAttribute('aria-valuenow', Math.floor(DOM.audioPlayer.currentTime).toString());
            }
        }
    });

    DOM.audioPlayer.addEventListener('error', (e) => {
        console.error('Audio error:', e);
        showError('Audio-Fehler', 'Die Audio-Datei konnte nicht geladen werden.');
        updatePlayButtonState(false);
    });
}

// Progress Bar Interaction
if (DOM.progressContainer && DOM.audioPlayer) {
    const seekAudio = (e) => {
        if (!DOM.audioPlayer.duration) return;

        const rect = DOM.progressContainer.getBoundingClientRect();
        const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        DOM.audioPlayer.currentTime = percent * DOM.audioPlayer.duration;
    };

    DOM.progressContainer.addEventListener('click', seekAudio);

    // Keyboard support for progress bar
    DOM.progressContainer.addEventListener('keydown', (e) => {
        if (!DOM.audioPlayer.duration) return;

        let newTime = DOM.audioPlayer.currentTime;

        if (e.key === 'ArrowLeft') {
            newTime = Math.max(0, newTime - 5);
            e.preventDefault();
        } else if (e.key === 'ArrowRight') {
            newTime = Math.min(DOM.audioPlayer.duration, newTime + 5);
            e.preventDefault();
        } else if (e.key === 'Home') {
            newTime = 0;
            e.preventDefault();
        } else if (e.key === 'End') {
            newTime = DOM.audioPlayer.duration;
            e.preventDefault();
        }

        DOM.audioPlayer.currentTime = newTime;
    });
}

// ===== SWIPE & NAVIGATION =====
const SwipeState = {
    touchStartX: 0,
    touchEndX: 0,
    touchStartY: 0,
    touchEndY: 0,
    isDragging: false
};

function handleSwipe(diffX, diffY) {
    if (Math.abs(diffX) > SWIPE_THRESHOLD && diffY < VERTICAL_THRESHOLD) {
        if (diffX > 0) {
            nextStory();
        } else {
            previousStory();
        }
    }
}

function nextStory() {
    if (AppState.stories.length === 0) return;
    if (AppState.playbackStartTime && AppState.currentStory) {
        const duration = (Date.now() - AppState.playbackStartTime) / 1000;
        trackPlaytime(AppState.currentStory.id, duration);
        AppState.playbackStartTime = null;
    }
    AppState.currentStoryIndex = (AppState.currentStoryIndex + 1) % AppState.stories.length;
    loadStory(AppState.stories[AppState.currentStoryIndex]);
}

function previousStory() {
    if (AppState.stories.length === 0) return;
    if (AppState.playbackStartTime && AppState.currentStory) {
        const duration = (Date.now() - AppState.playbackStartTime) / 1000;
        trackPlaytime(AppState.currentStory.id, duration);
        AppState.playbackStartTime = null;
    }
    AppState.currentStoryIndex = (AppState.currentStoryIndex - 1 + AppState.stories.length) % AppState.stories.length;
    loadStory(AppState.stories[AppState.currentStoryIndex]);
}

// Touch Events
if (DOM.storySlider) {
    DOM.storySlider.addEventListener('touchstart', (e) => {
        SwipeState.touchStartX = e.changedTouches[0].screenX;
        SwipeState.touchStartY = e.changedTouches[0].screenY;
        SwipeState.isDragging = true;
    }, { passive: true });

    DOM.storySlider.addEventListener('touchmove', (e) => {
        if (!SwipeState.isDragging) return;
        SwipeState.touchEndX = e.changedTouches[0].screenX;
        SwipeState.touchEndY = e.changedTouches[0].screenY;
    }, { passive: true });

    DOM.storySlider.addEventListener('touchend', () => {
        if (!SwipeState.isDragging) return;
        SwipeState.isDragging = false;

        const diffX = SwipeState.touchStartX - SwipeState.touchEndX;
        const diffY = Math.abs(SwipeState.touchStartY - SwipeState.touchEndY);
        handleSwipe(diffX, diffY);
    }, { passive: true });

    // Mouse Events (Desktop)
    DOM.storySlider.addEventListener('mousedown', (e) => {
        SwipeState.touchStartX = e.clientX;
        SwipeState.touchStartY = e.clientY;
        SwipeState.isDragging = true;
        DOM.storySlider.style.cursor = 'grabbing';
    });

    DOM.storySlider.addEventListener('mousemove', (e) => {
        if (!SwipeState.isDragging) return;
        SwipeState.touchEndX = e.clientX;
        SwipeState.touchEndY = e.clientY;
    });

    DOM.storySlider.addEventListener('mouseup', () => {
        if (!SwipeState.isDragging) return;
        SwipeState.isDragging = false;
        DOM.storySlider.style.cursor = 'grab';

        const diffX = SwipeState.touchStartX - SwipeState.touchEndX;
        const diffY = Math.abs(SwipeState.touchStartY - SwipeState.touchEndY);
        handleSwipe(diffX, diffY);
    });

    DOM.storySlider.addEventListener('mouseleave', () => {
        if (SwipeState.isDragging) {
            SwipeState.isDragging = false;
            DOM.storySlider.style.cursor = 'grab';
        }
    });
}

// ===== KEYBOARD NAVIGATION =====
document.addEventListener('keydown', (e) => {
    // Skip if user is typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    // Skip if menu is open and it's not Escape
    if (DOM.menu?.classList.contains('active') && e.key !== 'Escape') return;

    switch(e.key) {
        case 'ArrowLeft':
            e.preventDefault();
            previousStory();
            break;
        case 'ArrowRight':
            e.preventDefault();
            nextStory();
            break;
        case ' ':
            e.preventDefault();
            togglePlay();
            break;
    }
});

// Edge Indicators Click Handlers
if (DOM.swipeEdgeLeft) {
    DOM.swipeEdgeLeft.addEventListener('click', previousStory);
    DOM.swipeEdgeLeft.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            previousStory();
        }
    });
}

if (DOM.swipeEdgeRight) {
    DOM.swipeEdgeRight.addEventListener('click', nextStory);
    DOM.swipeEdgeRight.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            nextStory();
        }
    });
}

// ===== PREVENT PULL-TO-REFRESH =====
document.body.addEventListener('touchmove', (e) => {
    if (e.touches.length > 1) return;
    const touch = e.touches[0];
    if (touch.pageY > 100) return;
    e.preventDefault();
}, { passive: false });

// ===== ADMIN DASHBOARD =====
let adminChart = null;

function initAdminDashboard() {
    const chartCanvas = document.getElementById('playtimeChart');
    if (!chartCanvas) return;

    const periodButtons = document.querySelectorAll('.admin-period-button');

    async function loadAdminStats(period = '24h') {
        try {
            const response = await fetch(`/api/admin/stats?period=${period}`);
            if (!response.ok) {
                if (response.status === 401) {
                    window.location.href = '/admin/login';
                    return;
                }
                throw new Error('Failed to load stats');
            }

            const data = await response.json();
            updateAdminChart(data.stats);
        } catch (error) {
            console.error('Error loading admin stats:', error);
        }
    }

    function updateAdminChart(stats) {
        const labels = stats.map(s => s.label);
        const durations = stats.map(s => Math.round(s.value / 60));

        if (adminChart) {
            adminChart.data.labels = labels;
            adminChart.data.datasets[0].data = durations;
            adminChart.update();
        } else {
            adminChart = new Chart(chartCanvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Playtime (Minuten)',
                        data: durations,
                        backgroundColor: '#ff4444',
                        borderColor: '#ff3333',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#ffffff', font: { size: 14 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Playtime: ${context.parsed.y} min`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: '#ffffff',
                                callback: function(value) {
                                    return value + ' min';
                                }
                            },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            title: {
                                display: true,
                                text: 'Playtime (Minuten)',
                                color: '#ffffff'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#ffffff',
                                maxRotation: 45,
                                minRotation: 0
                            },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        }
                    }
                }
            });
        }
    }

    periodButtons.forEach(button => {
        button.addEventListener('click', () => {
            periodButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            loadAdminStats(button.dataset.period);
        });
    });

    loadAdminStats('24h');
}

// Track playtime on page unload
window.addEventListener('beforeunload', () => {
    if (AppState.playbackStartTime && AppState.currentStory && AppState.isPlaying) {
        const duration = (Date.now() - AppState.playbackStartTime) / 1000;
        navigator.sendBeacon('/api/playtime', JSON.stringify({
            story_id: AppState.currentStory.id,
            play_duration: Math.floor(duration)
        }));
    }
});

// ===== INITIALIZE APP =====
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        loadStories();
        initAdminDashboard();
    });
} else {
    loadStories();
    initAdminDashboard();
}
