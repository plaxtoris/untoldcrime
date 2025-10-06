// App State
let stories = [];
let currentStoryIndex = 0;
let currentStory = null;
let isPlaying = false;
let hasSwipedBefore = false;

// DOM Elements
const audioPlayer = document.getElementById('audioPlayer');
const playButton = document.getElementById('playButton');
const progressBar = document.getElementById('progressBar');
const progressContainer = document.getElementById('progressContainer');
const currentTimeDisplay = document.getElementById('currentTime');
const durationDisplay = document.getElementById('duration');
const coverImage = document.getElementById('coverImage');
const storyTitle = document.getElementById('storyTitle');
const storySummary = document.getElementById('storySummary');
const storySlider = document.getElementById('storySlider');
const menuButton = document.getElementById('menuButton');
const menu = document.getElementById('menu');
const swipeIndicator = document.getElementById('swipeIndicator');

// Menu Toggle
menuButton.addEventListener('click', () => {
    menu.classList.toggle('active');
});

menu.addEventListener('click', (e) => {
    if (e.target === menu) {
        menu.classList.remove('active');
    }
});

// Utility Functions
function formatTime(seconds) {
    if (!seconds || isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Load Stories
async function loadStories() {
    try {
        const response = await fetch('/api/stories');
        const data = await response.json();
        stories = data.stories;
        if (stories.length > 0) {
            currentStoryIndex = Math.floor(Math.random() * stories.length);
            loadStory(stories[currentStoryIndex]);
        }
    } catch (error) {
        console.error('Error loading stories:', error);
        storyTitle.textContent = 'Fehler beim Laden';
        storySummary.textContent = 'Bitte Seite neu laden';
    }
}

// Load Story
function loadStory(story) {
    if (!story) return;

    currentStory = story;
    coverImage.style.backgroundImage = `url('${story.cover_url}')`;
    storyTitle.textContent = story.title;
    storySummary.textContent = story.summary;

    audioPlayer.src = story.audio_url;
    audioPlayer.load();

    if (isPlaying) {
        isPlaying = false;
        playButton.classList.remove('playing');
    }

    progressBar.style.width = '0%';
    currentTimeDisplay.textContent = '00:00';
}

// Audio Player Controls
playButton.addEventListener('click', togglePlay);

function togglePlay() {
    if (!currentStory) return;

    if (isPlaying) {
        audioPlayer.pause();
    } else {
        audioPlayer.play();
    }
}

audioPlayer.addEventListener('play', () => {
    isPlaying = true;
    playButton.classList.add('playing');
});

audioPlayer.addEventListener('pause', () => {
    isPlaying = false;
    playButton.classList.remove('playing');
});

audioPlayer.addEventListener('ended', () => {
    isPlaying = false;
    playButton.classList.remove('playing');
    progressBar.style.width = '0%';
});

audioPlayer.addEventListener('loadedmetadata', () => {
    durationDisplay.textContent = formatTime(audioPlayer.duration);
});

audioPlayer.addEventListener('timeupdate', () => {
    if (audioPlayer.duration) {
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        progressBar.style.width = `${progress}%`;
        currentTimeDisplay.textContent = formatTime(audioPlayer.currentTime);
    }
});

// Progress Bar Click
progressContainer.addEventListener('click', (e) => {
    if (!audioPlayer.duration) return;
    const rect = progressContainer.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    audioPlayer.currentTime = percent * audioPlayer.duration;
});

// Swipe Functionality
let touchStartX = 0;
let touchEndX = 0;
let touchStartY = 0;
let touchEndY = 0;
let isDragging = false;

storySlider.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
    isDragging = true;
}, { passive: true });

storySlider.addEventListener('touchmove', (e) => {
    if (!isDragging) return;
    touchEndX = e.changedTouches[0].screenX;
    touchEndY = e.changedTouches[0].screenY;
}, { passive: true });

storySlider.addEventListener('touchend', () => {
    if (!isDragging) return;
    isDragging = false;

    const diffX = touchStartX - touchEndX;
    const diffY = Math.abs(touchStartY - touchEndY);

    // Only trigger swipe if horizontal movement is greater than vertical
    if (Math.abs(diffX) > 50 && diffY < 100) {
        if (!hasSwipedBefore) {
            hasSwipedBefore = true;
            if (swipeIndicator) {
                swipeIndicator.style.display = 'none';
            }
        }

        if (diffX > 0) {
            // Swiped left - next story
            nextStory();
        } else {
            // Swiped right - previous story
            previousStory();
        }
    }
}, { passive: true });

// Navigation Functions
function nextStory() {
    if (stories.length === 0) return;
    currentStoryIndex = (currentStoryIndex + 1) % stories.length;
    loadStory(stories[currentStoryIndex]);
}

function previousStory() {
    if (stories.length === 0) return;
    currentStoryIndex = (currentStoryIndex - 1 + stories.length) % stories.length;
    loadStory(stories[currentStoryIndex]);
}

// Keyboard Navigation (for desktop)
document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') {
        previousStory();
    } else if (e.key === 'ArrowRight') {
        nextStory();
    } else if (e.key === ' ') {
        e.preventDefault();
        togglePlay();
    }
});

// Prevent Pull-to-Refresh on Mobile
document.body.addEventListener('touchmove', (e) => {
    if (e.touches.length > 1) return;
    const touch = e.touches[0];
    if (touch.pageY > 100) return;
    e.preventDefault();
}, { passive: false });

// Initialize App
loadStories();
