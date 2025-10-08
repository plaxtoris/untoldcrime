"""Utility functions and helpers for the application."""

from pathlib import Path
from typing import Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def load_json(file_path: Path) -> Optional[dict[str, Any]]:
    """Load JSON data from a file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return None


def save_json(data: dict[str, Any], file_path: Path) -> bool:
    """Save data as JSON to a file.

    Args:
        data: Data to save
        file_path: Path where to save the JSON file

    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory(file_path.parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (OSError, TypeError) as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        return False


def format_time_seconds(seconds: float) -> str:
    """Format seconds into a human-readable string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string (e.g., "1h 23m 45s", "45.2s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"

    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m {remaining_seconds}s"
