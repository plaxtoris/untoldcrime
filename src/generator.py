"""Story generation orchestration."""

from pathlib import Path
from typing import Optional
from config import DATA_DIR
from cover import generate_cover
from llm import generate_story
from tts import synthesize_speech
from utils import save_json
import secrets
import logging

logger = logging.getLogger(__name__)


def generate_complete_story(
    model: str = "gemini-2.5-pro",
    word_limit: int = 4000,
    setting: str = "Bitcoin Darknet"
) -> Optional[dict[str, str]]:
    """Generate a complete story with audio and cover image.

    Args:
        model: LLM model to use
        word_limit: Target word count for the story
        setting: Story setting/theme

    Returns:
        Story metadata dictionary or None on failure
    """
    try:
        # Generate story text
        logger.info(f"Generating story: {setting}")
        story_data = generate_story(model=model, word_limit=word_limit, setting=setting)

        if not story_data:
            logger.error("Story generation failed")
            return None

        # Create output directory
        story_dir = DATA_DIR / secrets.token_hex(8)
        story_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created story directory: {story_dir}")

        # Generate cover image
        logger.info("Generating cover image")
        if not generate_cover(topic=story_data["summary"], output_dir=story_dir):
            logger.warning("Cover generation failed, continuing anyway")

        # Generate audio
        logger.info("Synthesizing speech")
        audio_path = story_dir / "story.wav"
        if not synthesize_speech(text=story_data["story"], output_path=audio_path):
            logger.error("Speech synthesis failed")
            return None

        # Save story metadata
        story_json_path = story_dir / "story.json"
        if not save_json(story_data, story_json_path):
            logger.warning("Failed to save story metadata")

        logger.info(f"Story generation complete: {story_dir}")
        return story_data

    except Exception as e:
        logger.error(f"Story generation failed: {e}")
        return None
