"""Text-to-speech synthesis using Google Cloud TTS."""

from google.api_core import exceptions
from google.cloud import texttospeech
from google.cloud import storage
from pydub import AudioSegment
from datetime import datetime
from pathlib import Path
from typing import Optional
from config import (
    TTS_VOICE_LANGUAGE,
    TTS_VOICE_NAME,
    TTS_RATE_LIMIT,
    TTS_TIME_WINDOW,
    TTS_MAX_RETRIES,
    TTS_RETRY_DELAY,
    GOOGLE_BUCKET_NAME,
    GOOGLE_PROJECT,
    GOOGLE_LOCATION,
    API_TIMEOUT
)
import threading
import uuid
import time
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API requests with sliding window."""

    def __init__(self, max_requests: int, time_window: int):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: list[datetime] = []
        self.lock = threading.Lock()

    def wait_if_needed(self) -> None:
        """Wait if rate limit is reached."""
        with self.lock:
            now = datetime.now()

            # Remove old requests outside time window
            self.requests = [
                req_time for req_time in self.requests
                if (now - req_time).total_seconds() < self.time_window
            ]

            if len(self.requests) >= self.max_requests:
                # Wait until oldest request is outside window
                oldest = self.requests[0]
                wait_time = self.time_window - (now - oldest).total_seconds()
                if wait_time > 0:
                    logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                    time.sleep(wait_time + 0.1)

                    # Clean up after waiting
                    now = datetime.now()
                    self.requests = [
                        req_time for req_time in self.requests
                        if (now - req_time).total_seconds() < self.time_window
                    ]

            self.requests.append(now)


# Global rate limiter instance
_rate_limiter = RateLimiter(max_requests=TTS_RATE_LIMIT, time_window=TTS_TIME_WINDOW)


def synthesize_speech(text: str, output_path: Path) -> bool:
    """Synthesize speech from text and save as MP3.

    Args:
        text: Text to synthesize
        output_path: Path where to save the audio file (should end in .wav)

    Returns:
        True if successful, False otherwise
    """
    wav_path = output_path.with_suffix('.wav')
    mp3_path = output_path.with_suffix('.mp3')

    try:
        # Generate audio
        gcs_filename = _generate_audio(text)
        if not gcs_filename:
            return False

        # Download from GCS
        if not _download_from_gcs(gcs_filename, wav_path):
            return False

        # Convert to MP3
        if not _convert_to_mp3(wav_path, mp3_path):
            return False

        logger.info(f"Speech synthesized successfully: {mp3_path}")
        return True

    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        return False


def _generate_audio(text: str) -> Optional[str]:
    """Generate audio using Google TTS API.

    Args:
        text: Text to synthesize

    Returns:
        GCS filename if successful, None otherwise
    """
    filename = f"{uuid.uuid4().hex[:32]}.wav"

    for attempt in range(TTS_MAX_RETRIES):
        try:
            # Apply rate limiting
            _rate_limiter.wait_if_needed()

            # Setup TTS request
            client = texttospeech.TextToSpeechLongAudioSynthesizeClient()
            input_text = texttospeech.SynthesisInput(text=text)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.LINEAR16
            )
            voice = texttospeech.VoiceSelectionParams(
                language_code=TTS_VOICE_LANGUAGE,
                name=TTS_VOICE_NAME
            )
            parent = f"projects/{GOOGLE_PROJECT}/locations/{GOOGLE_LOCATION}"
            output_uri = f"gs://{GOOGLE_BUCKET_NAME}/{filename}"

            request = texttospeech.SynthesizeLongAudioRequest(
                parent=parent,
                input=input_text,
                audio_config=audio_config,
                voice=voice,
                output_gcs_uri=output_uri
            )

            # Execute synthesis
            operation = client.synthesize_long_audio(request=request)
            operation.result(timeout=API_TIMEOUT)

            logger.info(f"Audio generated: {filename}")
            return filename

        except exceptions.ResourceExhausted:
            if attempt < TTS_MAX_RETRIES - 1:
                wait_time = TTS_RETRY_DELAY * (2 ** attempt)
                logger.warning(
                    f"Rate limit hit, retrying in {wait_time}s "
                    f"(attempt {attempt + 1}/{TTS_MAX_RETRIES})"
                )
                time.sleep(wait_time)
            else:
                logger.error("Max retries reached for TTS API")
                return None

        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None

    return None


def _download_from_gcs(filename: str, local_path: Path) -> bool:
    """Download file from Google Cloud Storage.

    Args:
        filename: Name of file in GCS bucket
        local_path: Local path where to save the file

    Returns:
        True if successful, False otherwise
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GOOGLE_BUCKET_NAME)
        blob = bucket.blob(filename)

        blob.download_to_filename(str(local_path))
        blob.delete()  # Clean up GCS

        logger.info(f"Downloaded from GCS: {filename}")
        return True

    except Exception as e:
        logger.error(f"Failed to download from GCS: {e}")
        return False


def _convert_to_mp3(wav_path: Path, mp3_path: Path) -> bool:
    """Convert WAV file to MP3.

    Args:
        wav_path: Path to input WAV file
        mp3_path: Path to output MP3 file

    Returns:
        True if successful, False otherwise
    """
    try:
        audio = AudioSegment.from_wav(str(wav_path))
        audio.export(str(mp3_path), format="mp3")

        # Clean up WAV file
        wav_path.unlink(missing_ok=True)

        logger.info(f"Converted to MP3: {mp3_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to convert to MP3: {e}")
        return False
