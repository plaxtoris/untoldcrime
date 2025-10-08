"""Application configuration and constants."""

from pathlib import Path
from typing import Final
import os

# Base paths
BASE_DIR: Final[Path] = Path(__file__).parent.parent
SRC_DIR: Final[Path] = BASE_DIR / "src"
DATA_DIR: Final[Path] = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_PATH: Final[Path] = DATA_DIR / "database.db"

# Google Cloud Configuration
GOOGLE_BUCKET: Final[str] = "gs://zalazium/"
GOOGLE_BUCKET_NAME: Final[str] = "zalazium"
GOOGLE_PROJECT: Final[str] = "zalazium-gmbh"
GOOGLE_LOCATION: Final[str] = "us-central1"
GOOGLE_CREDENTIALS_PATH: Final[Path] = BASE_DIR / "google.json"

# TTS Configuration
TTS_VOICE_LANGUAGE: Final[str] = "de-DE"
TTS_VOICE_NAME: Final[str] = "de-DE-Chirp3-HD-Gacrux"
TTS_RATE_LIMIT: Final[int] = 90
TTS_TIME_WINDOW: Final[int] = 60
TTS_MAX_RETRIES: Final[int] = 5
TTS_RETRY_DELAY: Final[int] = 1

# LLM Configuration
DEFAULT_MODEL: Final[str] = "gemini-2.5-pro"
DEFAULT_WORD_LIMIT: Final[int] = 4000

# API Configuration
LITELLM_MASTER_KEY: Final[str | None] = os.getenv("LITELLM_MASTER_KEY")
DOMAIN_WRAPPER: Final[str] = os.getenv("DOMAIN_WRAPPER", "http://localhost:8080")
API_TIMEOUT: Final[int] = 600

# Server Configuration
STATIC_DIR: Final[Path] = SRC_DIR / "static"
TEMPLATES_DIR: Final[Path] = SRC_DIR / "templates"
ADMIN_USER: Final[str] = os.getenv("USER", "admin")
ADMIN_PASSWORD: Final[str] = os.getenv("PASSWORD", "admin")
SESSION_DURATION_HOURS: Final[int] = 24

# Story Generation
MIN_STORY_DURATION_MIN: Final[float] = 10.0
MAX_STORY_DURATION_MIN: Final[float] = 45.0
