let themesData = {};
let currentThemeIndex = 0;
let currentTheme = null;
let currentPlaylist = [];
let lastPlayedIndex = -1;
let audioElement = null;
let isPlaying = false;
let playStartTime = null;
let currentTitle = null;
let touchStartX = 0;
let touchEndX = 0;
let touchStartY = 0;
let touchEndY = 0;
let touchStartTime = 0;
let themesArray = [];
let isTransitioning = false;
let isDragging = false;

document.addEventListener('DOMContentLoaded', async () => {
    audioElement = document.getElementById('audio-element');
    await loadThemes();
    setupSwipeListeners();
    setupPlayerControls();
});

async function loadThemes() {
    try {
        const response = await fetch('/api/themes');
        themesData = await response.json();
        themesArray = Object.keys(themesData);
        renderThemeSlides();

        // Start at position 1 because of clone at position 0
        const container = document.getElementById('themes-container');
        container.style.transform = `translateX(-100%)`;
        container.style.transition = 'none';

        selectRandomStory(currentThemeIndex);
    } catch (error) {
        console.error('Fehler beim Laden der Themen:', error);
    }
}

function renderThemeSlides() {
    const container = document.getElementById('themes-container');
    container.innerHTML = '';

    // Helper function to create a slide
    const createSlide = (theme, index) => {
        const slide = document.createElement('div');
        slide.className = 'theme-slide';
        slide.dataset.theme = theme;
        slide.dataset.index = index;

        // Set background image
        const imagePath = `/data/${theme}/image.jpg`;
        slide.style.backgroundImage = `url('${imagePath}')`;

        const textContent = document.createElement('div');
        textContent.className = 'theme-text-content';

        const nameEl = document.createElement('h2');
        nameEl.className = 'theme-name';
        nameEl.textContent = theme;

        const storyEl = document.createElement('p');
        storyEl.className = 'current-story';
        storyEl.id = `story-${index}`;
        storyEl.textContent = 'Geschichte wird geladen...';

        textContent.appendChild(nameEl);
        textContent.appendChild(storyEl);

        const controls = document.createElement('div');
        controls.className = 'player-controls';

        const playBtn = document.createElement('button');
        playBtn.className = 'play-btn';
        playBtn.id = `play-${index}`;
        playBtn.innerHTML = `
            <svg class="play-icon" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
            </svg>
            <svg class="pause-icon hidden" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16"/>
                <rect x="14" y="4" width="4" height="16"/>
            </svg>
        `;

        const nextBtn = document.createElement('button');
        nextBtn.className = 'next-btn';
        nextBtn.id = `next-${index}`;
        nextBtn.innerHTML = `
            <svg viewBox="0 0 24 24">
                <path d="M6 6v12l8-6z"/>
                <path d="M14 6v12l8-6z"/>
            </svg>
        `;

        controls.appendChild(playBtn);
        controls.appendChild(nextBtn);

        slide.appendChild(textContent);
        slide.appendChild(controls);

        // Add event listeners (iOS-compatible touch + click)
        const handlePlayTap = (e) => {
            e.stopPropagation();
            e.preventDefault();
            togglePlayPause(index);
        };
        const handleNextTap = (e) => {
            e.stopPropagation();
            e.preventDefault();
            playNextStory(index);
        };

        playBtn.addEventListener('touchend', handlePlayTap, {passive: false});
        playBtn.addEventListener('click', handlePlayTap);
        nextBtn.addEventListener('touchend', handleNextTap, {passive: false});
        nextBtn.addEventListener('click', handleNextTap);

        return slide;
    };

    // Add all slides
    themesArray.forEach((theme, index) => {
        container.appendChild(createSlide(theme, index));
    });

    // Clone first and last slides for seamless transition
    if (themesArray.length > 0) {
        const firstClone = createSlide(themesArray[0], 0);
        firstClone.classList.add('clone');
        const lastClone = createSlide(themesArray[themesArray.length - 1], themesArray.length - 1);
        lastClone.classList.add('clone');

        container.appendChild(firstClone);
        container.insertBefore(lastClone, container.firstChild);
    }
}

function setupSwipeListeners() {
    const carousel = document.getElementById('theme-carousel');
    const leftIndicator = document.querySelector('.swipe-indicator.left');
    const rightIndicator = document.querySelector('.swipe-indicator.right');

    // Touch events with better click detection
    carousel.addEventListener('touchstart', handleTouchStart, {passive: false});
    carousel.addEventListener('touchmove', handleTouchMove, {passive: false});
    carousel.addEventListener('touchend', handleTouchEnd);

    // Mouse events for desktop with drag detection
    let mouseDown = false;
    carousel.addEventListener('mousedown', (e) => {
        // Ignore if clicking on buttons or controls
        if (e.target.closest('.play-btn') || e.target.closest('.next-btn') ||
            e.target.closest('.swipe-indicator')) {
            return;
        }

        mouseDown = true;
        isDragging = false;
        touchStartX = e.clientX;
        touchStartY = e.clientY;
        touchStartTime = Date.now();
        e.preventDefault();
    });

    carousel.addEventListener('mousemove', (e) => {
        if (mouseDown) {
            const deltaX = Math.abs(e.clientX - touchStartX);
            const deltaY = Math.abs(e.clientY - touchStartY);

            // Mark as dragging if moved more than 10px
            if (deltaX > 10 || deltaY > 10) {
                isDragging = true;
                touchEndX = e.clientX;
                touchEndY = e.clientY;
                e.preventDefault();
            }
        }
    });

    carousel.addEventListener('mouseup', (e) => {
        if (mouseDown) {
            mouseDown = false;

            // Only handle swipe if we were dragging
            if (isDragging) {
                handleSwipe();
            }
            isDragging = false;
        }
    });

    carousel.addEventListener('mouseleave', () => {
        mouseDown = false;
        isDragging = false;
    });

    // Touch and click handlers for indicators (iOS-compatible)
    let indicatorTouchHandled = false;

    const handleIndicatorTouchStart = (direction) => (e) => {
        e.stopPropagation();
        e.preventDefault();
        indicatorTouchHandled = true;
        navigateTheme(direction);
    };

    const handleIndicatorClick = (direction) => (e) => {
        e.stopPropagation();
        e.preventDefault();
        // Only handle click if touch wasn't already handled
        if (!indicatorTouchHandled) {
            navigateTheme(direction);
        }
        indicatorTouchHandled = false;
    };

    // Left indicator
    leftIndicator.addEventListener('touchstart', handleIndicatorTouchStart(-1), {passive: false});
    leftIndicator.addEventListener('click', handleIndicatorClick(-1));

    // Right indicator
    rightIndicator.addEventListener('touchstart', handleIndicatorTouchStart(1), {passive: false});
    rightIndicator.addEventListener('click', handleIndicatorClick(1));

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') navigateTheme(-1);
        if (e.key === 'ArrowRight') navigateTheme(1);
    });
}

function handleTouchStart(e) {
    // Ignore if touching buttons or controls
    const target = e.target.closest('.play-btn, .next-btn, .swipe-indicator');
    if (target) {
        // Don't interfere with button touches - stop propagation completely
        e.stopPropagation();
        return;
    }

    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
    touchStartTime = Date.now();
    isDragging = false;
}

function handleTouchMove(e) {
    if (!touchStartX) return;

    touchEndX = e.touches[0].clientX;
    touchEndY = e.touches[0].clientY;

    const deltaX = Math.abs(touchEndX - touchStartX);
    const deltaY = Math.abs(touchEndY - touchStartY);

    // If horizontal movement is greater than vertical, it's a swipe
    if (deltaX > 10 && deltaX > deltaY) {
        isDragging = true;
        e.preventDefault(); // Prevent scrolling
    }
}

function handleTouchEnd(e) {
    if (!touchStartX) return;

    // Only handle swipe if we were dragging
    if (isDragging) {
        handleSwipe();
    }

    // Reset
    touchStartX = 0;
    touchStartY = 0;
    isDragging = false;
}

function handleSwipe() {
    const swipeDistance = touchStartX - touchEndX;
    const verticalDistance = Math.abs(touchStartY - touchEndY);
    const minSwipeDistance = 80; // Increased from 50 to 80
    const maxVerticalDistance = 100; // Max vertical movement allowed
    const swipeTime = Date.now() - touchStartTime;
    const maxSwipeTime = 500; // Max 500ms for a swipe

    // Only register as swipe if:
    // 1. Horizontal distance is enough
    // 2. Vertical distance is not too much (to avoid diagonal swipes)
    // 3. Swipe was quick enough
    if (Math.abs(swipeDistance) > minSwipeDistance &&
        verticalDistance < maxVerticalDistance &&
        swipeTime < maxSwipeTime) {
        if (swipeDistance > 0) {
            navigateTheme(1); // Swipe left - next theme
        } else {
            navigateTheme(-1); // Swipe right - previous theme
        }
    }
}

function navigateTheme(direction) {
    if (isTransitioning) return;

    // Track playtime before switching
    trackPlaytime();

    isTransitioning = true;
    const container = document.getElementById('themes-container');

    // Calculate visual position (including clone offset)
    let visualIndex = currentThemeIndex + 1; // +1 because of clone at start
    visualIndex += direction;

    // Animate to new position
    container.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    container.style.transform = `translateX(-${visualIndex * 100}%)`;

    // Update logical index
    currentThemeIndex += direction;

    // Handle wrap-around logic after animation
    setTimeout(() => {
        container.style.transition = 'none';

        if (currentThemeIndex < 0) {
            currentThemeIndex = themesArray.length - 1;
            container.style.transform = `translateX(-${themesArray.length * 100}%)`;
        } else if (currentThemeIndex >= themesArray.length) {
            currentThemeIndex = 0;
            container.style.transform = `translateX(-100%)`;
        }

        isTransitioning = false;
    }, 300);

    // Update current theme data
    currentTheme = themesArray[currentThemeIndex];
    currentPlaylist = themesData[currentTheme];

    // Stop current audio
    if (!audioElement.paused) {
        audioElement.pause();
        updatePlayPauseButton(currentThemeIndex, false);
    }

    // Load new story
    selectRandomStory(currentThemeIndex);
}

function selectRandomStory(themeIndex) {
    const theme = themesArray[themeIndex];
    const playlist = themesData[theme];

    if (!playlist || playlist.length === 0) return;

    const randomIndex = Math.floor(Math.random() * playlist.length);
    const story = playlist[randomIndex];

    // Update story display
    const storyEl = document.getElementById(`story-${themeIndex}`);
    if (storyEl) {
        storyEl.textContent = story.titel;
    }

    // Prepare audio but don't play
    if (themeIndex === currentThemeIndex) {
        const audioUrl = `/api/audio/${theme}/${encodeURIComponent(story.titel)}`;
        audioElement.src = audioUrl;
        currentTitle = story.titel;
        lastPlayedIndex = randomIndex;
    }
}

function playNextStory(themeIndex) {
    if (themeIndex !== currentThemeIndex) return;

    const theme = themesArray[themeIndex];
    const playlist = themesData[theme];

    if (!playlist || playlist.length === 0) return;

    // Track current playtime before switching
    trackPlaytime();

    let newIndex;
    if (playlist.length === 1) {
        newIndex = 0;
    } else {
        do {
            newIndex = Math.floor(Math.random() * playlist.length);
        } while (newIndex === lastPlayedIndex);
    }

    lastPlayedIndex = newIndex;
    const story = playlist[newIndex];

    // Update story display
    const storyEl = document.getElementById(`story-${themeIndex}`);
    if (storyEl) {
        storyEl.textContent = story.titel;
    }

    // Load and play new story
    const audioUrl = `/api/audio/${theme}/${encodeURIComponent(story.titel)}`;
    audioElement.src = audioUrl;
    currentTitle = story.titel;
    playStartTime = null;
    audioElement.play();
    updatePlayPauseButton(themeIndex, true);
}

function togglePlayPause(themeIndex) {
    if (themeIndex !== currentThemeIndex) return;

    if (!audioElement.src || audioElement.src === '') {
        selectRandomStory(themeIndex);
    }

    if (audioElement.paused) {
        audioElement.play();
        updatePlayPauseButton(themeIndex, true);
    } else {
        audioElement.pause();
        updatePlayPauseButton(themeIndex, false);
    }
}

function updatePlayPauseButton(themeIndex, playing) {
    const playBtn = document.getElementById(`play-${themeIndex}`);
    if (!playBtn) return;

    const playIcon = playBtn.querySelector('.play-icon');
    const pauseIcon = playBtn.querySelector('.pause-icon');

    if (playing) {
        playIcon.classList.add('hidden');
        pauseIcon.classList.remove('hidden');
    } else {
        playIcon.classList.remove('hidden');
        pauseIcon.classList.add('hidden');
    }
}

function setupPlayerControls() {
    audioElement.addEventListener('play', () => {
        if (!playStartTime) {
            playStartTime = Date.now();
        }
        updatePlayPauseButton(currentThemeIndex, true);
    });

    audioElement.addEventListener('pause', () => {
        trackPlaytime();
        updatePlayPauseButton(currentThemeIndex, false);
    });

    audioElement.addEventListener('ended', () => {
        trackPlaytime();
        playNextStory(currentThemeIndex);
    });

    audioElement.volume = 0.7;

    audioElement.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        return false;
    });

    audioElement.controlsList = 'nodownload';
}

function trackPlaytime() {
    if (playStartTime && currentTheme && currentTitle) {
        const duration = Math.floor((Date.now() - playStartTime) / 1000);
        if (duration > 0) {
            fetch('/api/track-playtime', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    theme: currentTheme,
                    title: currentTitle,
                    duration: duration
                })
            }).catch(err => console.error('Tracking error:', err));
        }
        playStartTime = null;
    }
}

window.addEventListener('beforeunload', () => {
    trackPlaytime();
});