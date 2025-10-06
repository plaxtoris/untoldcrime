from google.api_core import exceptions
from google.cloud import texttospeech
from google.cloud import storage
from pydub import AudioSegment
from datetime import datetime
import threading
import uuid
import time
import os


# Rate limiter for Google TTS API
class RateLimiter:
    def __init__(self, max_requests=90, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = threading.Lock()

    def wait_if_needed(self):
        with self.lock:
            now = datetime.now()
            # Remove old requests outside time window
            self.requests = [req_time for req_time in self.requests if (now - req_time).total_seconds() < self.time_window]

            if len(self.requests) >= self.max_requests:
                # Wait until oldest request is outside window
                oldest = self.requests[0]
                wait_time = self.time_window - (now - oldest).total_seconds()
                if wait_time > 0:
                    time.sleep(wait_time + 0.1)
                    # Clean up after waiting
                    now = datetime.now()
                    self.requests = [req_time for req_time in self.requests if (now - req_time).total_seconds() < self.time_window]

            self.requests.append(now)


tts_rate_limiter = RateLimiter(max_requests=90, time_window=60)


def speak(text, filepath):
    max_retries = 5
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            # Apply rate limiting
            tts_rate_limiter.wait_if_needed()

            # tts
            filename = f"{str(uuid.uuid4()).replace('-', '')[:32]}.wav"
            client = texttospeech.TextToSpeechLongAudioSynthesizeClient()
            input = texttospeech.SynthesisInput(text=text)
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)
            voice = texttospeech.VoiceSelectionParams(language_code="de-DE", name="de-DE-Chirp3-HD-Gacrux")
            parent = f"projects/zalazium-gmbh/locations/us-central1"
            request = texttospeech.SynthesizeLongAudioRequest(parent=parent, input=input, audio_config=audio_config, voice=voice, output_gcs_uri=f"gs://zalazium/{filename}")
            operation = client.synthesize_long_audio(request=request)
            result = operation.result(timeout=600)
            break  # Success, exit retry loop
        except exceptions.ResourceExhausted as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2**attempt)  # Exponential backoff
                print(f"Rate limit hit, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise

    # download from bucket and delete
    storage_client = storage.Client()
    bucket = storage_client.bucket("zalazium")
    blob = bucket.blob(filename)
    blob.download_to_filename(filepath)
    blob.delete()

    # convert to mp3 and delete old wav
    audio = AudioSegment.from_wav(filepath)
    mp3_path = filepath.replace(".wav", ".mp3")
    audio.export(mp3_path, format="mp3")
    os.remove(filepath)
