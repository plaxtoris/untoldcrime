let authHeader = null;
let currentPeriod = '24h';
let chart = null;

// Check for stored credentials on page load
window.addEventListener('DOMContentLoaded', async () => {
    const storedAuth = localStorage.getItem('adminAuth');
    if (storedAuth) {
        authHeader = storedAuth;
        try {
            const response = await fetch('/api/admin/login', {
                method: 'POST',
                headers: {
                    'Authorization': authHeader
                }
            });
            
            if (response.ok) {
                document.getElementById('login-container').style.display = 'none';
                document.getElementById('admin-container').style.display = 'block';
                setupLogout();
                loadStats(currentPeriod);
            } else {
                // Invalid stored credentials, remove them
                localStorage.removeItem('adminAuth');
                authHeader = null;
            }
        } catch (error) {
            // Error with stored credentials, remove them
            localStorage.removeItem('adminAuth');
            authHeader = null;
        }
    }
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const credentials = btoa(`${username}:${password}`);
    authHeader = `Basic ${credentials}`;
    
    try {
        const response = await fetch('/api/admin/login', {
            method: 'POST',
            headers: {
                'Authorization': authHeader
            }
        });
        
        if (response.ok) {
            // Store credentials in localStorage
            localStorage.setItem('adminAuth', authHeader);
            document.getElementById('login-container').style.display = 'none';
            document.getElementById('admin-container').style.display = 'block';
            loadStats(currentPeriod);
        } else {
            document.getElementById('login-error').textContent = 'Falsches Passwort';
        }
    } catch (error) {
        document.getElementById('login-error').textContent = 'Fehler beim Login';
    }
});

document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentPeriod = btn.dataset.period;
        loadStats(currentPeriod);
    });
});

// formatTime and formatDuration functions are now imported from utils.js

async function loadStats(period) {
    try {
        const response = await fetch(`/api/admin/stats/${period}`, {
            headers: {
                'Authorization': authHeader
            }
        });
        
        if (!response.ok) throw new Error('Failed to load stats');
        
        const data = await response.json();
        
        // Update total time
        document.getElementById('total-time').textContent = formatTime(data.total_seconds);
        
        // Update chart
        updateChart(data.daily_data, period);
        
        // Update theme stats
        updateThemeStats(data.theme_stats);
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function updateChart(dailyData, period) {
    const ctx = document.getElementById('playtime-chart').getContext('2d');
    
    // Prepare data
    const labels = [];
    const values = [];
    
    dailyData.forEach(([date, seconds]) => {
        if (period === '24h') {
            // Show hour for 24h view
            const hour = new Date(date).getHours();
            labels.push(`${hour}:00`);
        } else {
            // Show date for other views
            const d = new Date(date);
            labels.push(`${d.getDate()}.${d.getMonth() + 1}`);
        }
        values.push(Math.round(seconds / 60)); // Convert to minutes
    });
    
    if (chart) {
        chart.destroy();
    }
    
    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Playtime (Minuten)',
                data: values,
                backgroundColor: 'rgba(75, 192, 192, 0.8)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    ticks: {
                        padding: 10
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + ' min';
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const minutes = context.parsed.y;
                            if (minutes < 60) {
                                return `${minutes} Minuten`;
                            }
                            const hours = Math.floor(minutes / 60);
                            const mins = minutes % 60;
                            return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
                        }
                    }
                }
            }
        }
    });
}

// Logout functionality
function setupLogout() {
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
            // Clear stored credentials
            localStorage.removeItem('adminAuth');
            authHeader = null;
            
            // Reload page to show login form
            window.location.reload();
        });
    }
}

function updateThemeStats(themeStats) {
    const container = document.getElementById('theme-list');
    container.innerHTML = '';
    
    if (themeStats.length === 0) {
        container.innerHTML = '<div class="no-data">Keine Daten vorhanden</div>';
        return;
    }
    
    themeStats.forEach((theme, index) => {
        const item = document.createElement('div');
        item.className = 'theme-item';
        
        const rank = document.createElement('div');
        rank.className = 'theme-rank';
        rank.textContent = `#${index + 1}`;
        
        const name = document.createElement('div');
        name.className = 'theme-name';
        name.textContent = theme.theme;
        
        const stats = document.createElement('div');
        stats.className = 'theme-stats-wrapper';
        
        const time = document.createElement('div');
        time.className = 'theme-time';
        time.textContent = formatTime(theme.seconds);
        
        const count = document.createElement('div');
        count.className = 'theme-count';
        count.textContent = `${theme.count} plays`;
        
        stats.appendChild(time);
        stats.appendChild(count);
        
        item.appendChild(rank);
        item.appendChild(name);
        item.appendChild(stats);
        
        container.appendChild(item);
    });
}