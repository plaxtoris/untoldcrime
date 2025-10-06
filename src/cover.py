from google.auth.transport.requests import Request
from google.oauth2 import service_account
from config import DATA_DIR
import requests
import time
import json
import os


def cover(topic, dir, model="imagen-4.0-generate-001", location="us-central1", number_of_images=1, aspect_ratio="1:1"):
    # Auth
    prompt = f"""Create an extremely appealing cover image for a true crime audio web app about: {topic}

    IMPORTANT: NO TEXT, NO LETTERS, NO WORDS, NO TYPOGRAPHY whatsoever!
    Visual imagery only. Pure photographic/artistic composition without any text elements.
    Focus on atmospheric mood, dark tones, and visual symbolism related to the topic."""

    file_path = os.path.join(os.path.dirname(__file__), "..", "google.json")
    creds = service_account.Credentials.from_service_account_file(file_path, scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(Request())

    # Richtiger Endpoint für Imagen
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/zalazium-gmbh/locations/{location}/publishers/google/models/{model}:predict"

    # Korrekte Payload-Struktur für Imagen
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

    response = requests.post(url, headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}, json=payload)

    try:
        data = response.json()
        if "predictions" in data:
            # Die Bilder sind base64-codiert
            import base64

            for i, prediction in enumerate(data["predictions"]):
                if "bytesBase64Encoded" in prediction:
                    # Decode base64 and save image
                    image_data = base64.b64decode(prediction["bytesBase64Encoded"])
                    file = os.path.join(dir, f"cover.png" if i == 0 else f"cover_{i}.png")
                    print(f"cover saved: {file}")
                    with open(file, "wb") as f:
                        f.write(image_data)
        else:
            print(f"Unerwartete Antwort: {data}")
    except Exception as e:
        print(f"Fehler: {response.status_code} - {response.text}")
        print(f"Exception: {e}")


if __name__ == "__main__":
    t0 = time.time()
    os.system("clear")
    cover(topic="Biene mit blauem Hut!")
    print(f"Time elapsed: {time.time() - t0:.1f} s")
