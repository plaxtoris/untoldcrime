# Legacy database module - now uses db_service for all operations
from db_service import db_service

# Maintain backward compatibility
def init_db():
    pass  # Initialization now handled by db_service

def track_playtime(theme, title, duration_seconds):
    return db_service.track_playtime(theme, title, duration_seconds)

def get_playtime_stats(period="alltime"):
    return db_service.get_playtime_stats(period)

def get_data():
    return db_service.get_data()
