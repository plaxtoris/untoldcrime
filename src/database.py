import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import DATABASE_PATH

# Timezone für Deutschland (automatische Sommer-/Winterzeit)
TIMEZONE = ZoneInfo("Europe/Berlin")


def init_database():
    """Initialize the database with required tables and indexes."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    # Create playtime_stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playtime_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id TEXT NOT NULL,
            play_duration INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON playtime_stats(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_story_id ON playtime_stats(story_id)")

    conn.commit()
    conn.close()


def get_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def track_playtime(story_id: str, play_duration: int):
    """Record playtime for a story."""
    if not story_id or play_duration < 0:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Speichere mit deutscher Zeit
        now = datetime.now(TIMEZONE)
        cursor.execute(
            "INSERT INTO playtime_stats (story_id, play_duration, timestamp) VALUES (?, ?, ?)",
            (story_id, play_duration, now.strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error tracking playtime: {e}")
        return False
    finally:
        conn.close()


def get_stats_by_period(period: str = "24h"):
    """Get aggregated playtime statistics by time period."""
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now(TIMEZONE)
    stats = []

    try:
        if period == "24h":
            # Last 24 hours, grouped by hour
            for i in range(24):
                hour_start = (now - timedelta(hours=23-i)).replace(minute=0, second=0, microsecond=0)
                hour_end = hour_start + timedelta(hours=1)

                cursor.execute("""
                    SELECT COALESCE(SUM(play_duration), 0) as total_duration
                    FROM playtime_stats
                    WHERE timestamp >= ? AND timestamp < ?
                """, (hour_start.strftime("%Y-%m-%d %H:%M:%S"), hour_end.strftime("%Y-%m-%d %H:%M:%S")))

                row = cursor.fetchone()
                stats.append({
                    "label": hour_start.strftime("%H:%M"),
                    "value": row["total_duration"] if row else 0
                })

        elif period == "7d":
            # Last 7 days, grouped by day
            for i in range(7):
                day_start = (now - timedelta(days=6-i)).replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)

                cursor.execute("""
                    SELECT COALESCE(SUM(play_duration), 0) as total_duration
                    FROM playtime_stats
                    WHERE timestamp >= ? AND timestamp < ?
                """, (day_start.strftime("%Y-%m-%d %H:%M:%S"), day_end.strftime("%Y-%m-%d %H:%M:%S")))

                row = cursor.fetchone()
                weekday = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][day_start.weekday()]
                stats.append({
                    "label": f"{weekday} {day_start.strftime('%d.%m')}",
                    "value": row["total_duration"] if row else 0
                })

        elif period == "30d":
            # Last 30 days, grouped by day
            for i in range(30):
                day_start = (now - timedelta(days=29-i)).replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)

                cursor.execute("""
                    SELECT COALESCE(SUM(play_duration), 0) as total_duration
                    FROM playtime_stats
                    WHERE timestamp >= ? AND timestamp < ?
                """, (day_start.strftime("%Y-%m-%d %H:%M:%S"), day_end.strftime("%Y-%m-%d %H:%M:%S")))

                row = cursor.fetchone()
                stats.append({
                    "label": day_start.strftime("%d.%m"),
                    "value": row["total_duration"] if row else 0
                })

        else:  # alltime
            # Get earliest record
            cursor.execute("SELECT MIN(timestamp) as earliest FROM playtime_stats")
            earliest_row = cursor.fetchone()

            if earliest_row and earliest_row["earliest"]:
                # Parse als deutsche Zeit
                earliest = datetime.strptime(earliest_row["earliest"], "%Y-%m-%d %H:%M:%S")
                earliest = earliest.replace(tzinfo=TIMEZONE)

                # Group by month from earliest to now
                current = earliest.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                while current <= now:
                    month_end = (current + timedelta(days=32)).replace(day=1)

                    cursor.execute("""
                        SELECT COALESCE(SUM(play_duration), 0) as total_duration
                        FROM playtime_stats
                        WHERE timestamp >= ? AND timestamp < ?
                    """, (current.strftime("%Y-%m-%d %H:%M:%S"), month_end.strftime("%Y-%m-%d %H:%M:%S")))

                    row = cursor.fetchone()
                    month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
                    stats.append({
                        "label": f"{month_names[current.month-1]} {current.strftime('%y')}",
                        "value": row["total_duration"] if row else 0
                    })

                    current = month_end

    finally:
        conn.close()

    return stats
