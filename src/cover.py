"""Cover image generation using Google Imagen."""

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from pathlib import Path
from typing import Optional
from config import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_PROJECT,
    GOOGLE_LOCATION
)
import requests
import base64
import logging

logger = logging.getLogger(__name__)


def generate_cover(
    topic: str,
    output_dir: Path,
    model: str = "imagen-4.0-generate-001",
    number_of_images: int = 1,
    aspect_ratio: str = "1:1"
) -> bool:
    """Generate a cover image using Google Imagen.

    Args:
        topic: Topic/description for the image
        output_dir: Directory where to save the image
        model: Imagen model to use
        number_of_images: Number of images to generate
        aspect_ratio: Image aspect ratio

    Returns:
        True if successful, False otherwise
    """
    try:
        # Generate prompt
        prompt = _build_prompt(topic)

        # Get authentication
        creds = _get_credentials()
        if not creds:
            return False

        # Make API request
        predictions = _call_imagen_api(
            creds=creds,
            prompt=prompt,
            model=model,
            number_of_images=number_of_images,
            aspect_ratio=aspect_ratio
        )

        if not predictions:
            return False

        # Save images
        return _save_images(predictions, output_dir)

    except Exception as e:
        logger.error(f"Cover generation failed: {e}")
        return False


def _build_prompt(topic: str) -> str:
    """Build the image generation prompt.

    Args:
        topic: Topic for the image

    Returns:
        Formatted prompt
    """
    return f"""Create an extremely appealing cover image for a true crime audio web app about: {topic}

    VERY IMPORTANT: NO TEXT, NO LETTERS, NO WORDS, NO TYPOGRAPHY whatsoever!
    Visual imagery only. Pure photographic/artistic composition without any text elements.
    Focus on atmospheric mood, dark tones, and visual symbolism related to the topic."""


def _get_credentials() -> Optional[service_account.Credentials]:
    """Get Google Cloud credentials.

    Returns:
        Credentials object or None if authentication fails
    """
    try:
        if not GOOGLE_CREDENTIALS_PATH.exists():
            logger.error(f"Credentials file not found: {GOOGLE_CREDENTIALS_PATH}")
            return None

        creds = service_account.Credentials.from_service_account_file(
            str(GOOGLE_CREDENTIALS_PATH),
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        creds.refresh(Request())
        return creds

    except Exception as e:
        logger.error(f"Failed to get credentials: {e}")
        return None


def _call_imagen_api(
    creds: service_account.Credentials,
    prompt: str,
    model: str,
    number_of_images: int,
    aspect_ratio: str
) -> Optional[list[dict]]:
    """Call the Imagen API.

    Args:
        creds: Google Cloud credentials
        prompt: Image generation prompt
        model: Model identifier
        number_of_images: Number of images to generate
        aspect_ratio: Image aspect ratio

    Returns:
        List of predictions or None on failure
    """
    try:
        url = (
            f"https://{GOOGLE_LOCATION}-aiplatform.googleapis.com/v1/"
            f"projects/{GOOGLE_PROJECT}/locations/{GOOGLE_LOCATION}/"
            f"publishers/google/models/{model}:predict"
        )

        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": number_of_images,
                "aspectRatio": aspect_ratio,
                "outputImageResolution": "2048x2048",
                "negativePrompt": "",
                "personGeneration": "allow_all",
                "safetyFilterLevel": "block_few",
                "addWatermark": False,
            },
        }

        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        if "predictions" not in data:
            logger.error(f"Unexpected API response: {data}")
            return None

        return data["predictions"]

    except requests.RequestException as e:
        logger.error(f"Imagen API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Imagen API: {e}")
        return None


def _save_images(predictions: list[dict], output_dir: Path) -> bool:
    """Save generated images to disk.

    Args:
        predictions: List of predictions from Imagen API
        output_dir: Directory where to save images

    Returns:
        True if at least one image was saved successfully
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_count = 0

    for i, prediction in enumerate(predictions):
        if "bytesBase64Encoded" not in prediction:
            logger.warning(f"Prediction {i} missing base64 data")
            continue

        try:
            image_data = base64.b64decode(prediction["bytesBase64Encoded"])
            filename = "cover.png" if i == 0 else f"cover_{i}.png"
            filepath = output_dir / filename

            with open(filepath, "wb") as f:
                f.write(image_data)

            logger.info(f"Cover image saved: {filepath}")
            saved_count += 1

        except Exception as e:
            logger.error(f"Failed to save image {i}: {e}")

    return saved_count > 0
