from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_PATH = DATA_DIR / "database.db"

# Google Cloud
GOOGLE_BUCKET = "gs://zalazium/"
GOOGLE_PROJECT = "zalazium-gmbh"
GOOGLE_LOCATION = "us-central1"

# TTS Configuration
TTS_VOICE_LANGUAGE = "de-DE"
TTS_VOICE_NAME = "de-DE-Chirp3-HD-Leda"
TTS_RATE_LIMIT = 90
TTS_TIME_WINDOW = 60

# API Configuration
LITELLM_MASTER_KEY = os.getenv("LITELLM_MASTER_KEY")
DOMAIN_WRAPPER = os.getenv("DOMAIN_WRAPPER", "http://localhost:8080")

# Server Configuration
STATIC_DIR = SRC_DIR / "static"
TEMPLATES_DIR = SRC_DIR / "templates"
