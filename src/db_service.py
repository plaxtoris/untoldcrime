from config import DATABASE_PATH, DATA_DIR
from datetime import datetime, timedelta
from contextlib import contextmanager
from pathlib import Path
import sqlite3


class DatabaseService:
    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE_PATH
        self._init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS playtime_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    theme TEXT NOT NULL,
                    title TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp ON playtime_tracking(timestamp)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_theme ON playtime_tracking(theme)
            """
            )

            conn.commit()

    def track_playtime(self, theme, title, duration_seconds):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO playtime_tracking (theme, title, duration_seconds) VALUES (?, ?, ?)", (theme, title, duration_seconds))
            conn.commit()

    def get_playtime_stats(self, period="alltime"):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build date filter with proper parameterization
            where_clause = ""
            params = []

            if period == "24h":
                cutoff_date = datetime.now() - timedelta(days=1)
                where_clause = "WHERE timestamp >= ?"
                params = [cutoff_date.isoformat()]
            elif period == "7d":
                cutoff_date = datetime.now() - timedelta(days=7)
                where_clause = "WHERE timestamp >= ?"
                params = [cutoff_date.isoformat()]
            elif period == "30d":
                cutoff_date = datetime.now() - timedelta(days=30)
                where_clause = "WHERE timestamp >= ?"
                params = [cutoff_date.isoformat()]

            # Total playtime
            query = f"SELECT COALESCE(SUM(duration_seconds), 0) as total_seconds FROM playtime_tracking {where_clause}"
            cursor.execute(query, params)
            total_seconds = cursor.fetchone()[0]

            # Daily/hourly playtime for chart
            if period == "24h":
                query = f"""
                    SELECT 
                        strftime('%Y-%m-%d %H:00', timestamp) as period,
                        SUM(duration_seconds) as seconds
                    FROM playtime_tracking
                    {where_clause}
                    GROUP BY strftime('%Y-%m-%d %H', timestamp)
                    ORDER BY period
                """
            else:
                query = f"""
                    SELECT 
                        DATE(timestamp) as period,
                        SUM(duration_seconds) as seconds
                    FROM playtime_tracking
                    {where_clause}
                    GROUP BY DATE(timestamp)
                    ORDER BY period
                """

            cursor.execute(query, params)
            daily_data = cursor.fetchall()

            # Theme statistics
            query = f"""
                SELECT 
                    theme,
                    SUM(duration_seconds) as total_seconds,
                    COUNT(*) as play_count
                FROM playtime_tracking
                {where_clause}
                GROUP BY theme
                ORDER BY total_seconds DESC
            """
            cursor.execute(query, params)
            theme_stats = cursor.fetchall()

            return {
                "total_seconds": total_seconds,
                "daily_data": [(row["period"], row["seconds"]) for row in daily_data],
                "theme_stats": [{"theme": row["theme"], "seconds": row["total_seconds"], "count": row["play_count"]} for row in theme_stats],
            }

    def get_data(self):
        return [{"theme": d.name, "titel": f.stem, "path": str(f)} for d in Path(DATA_DIR).iterdir() if d.is_dir() for f in d.glob("*.mp3")]


# Singleton instance
db_service = DatabaseService()
