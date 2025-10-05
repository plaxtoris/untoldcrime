from google.auth.transport.requests import Request
from google.oauth2 import service_account
from helper import DATA_DIR
import requests
import time
import json
import os


def chat_litellm(prompt, model="azure-gpt-4o", response_format={}):
    endpoint_url = os.getenv("LITELLM_URL") + "/v1/chat/completions"
    headers = {"Authorization": f"Bearer {os.getenv("LITELLM_MASTER_KEY")}", "Content-Type": "application/json"}
    data = {"model": model, "messages": [{"role": "user", "content": prompt}]}

    # json mode
    if response_format:
        prompt = f"""Du hilfst mir dabei Daten zu extrahieren und diese als json zu formatieren. 
        - Antworte IMMER mit genau diesen Keys: {list(response_format.keys())}. 
        - Antworte IMMER im JSON Format mit diesem Schema: {response_format}
        - Hier die Daten zum verarbeiten; {prompt}
        """
        data = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        data["response_format"] = response_format
    else:
        data = {"model": model, "messages": [{"role": "user", "content": prompt}]}

    response = requests.post(endpoint_url, headers=headers, json=data)
    if response.status_code == 200:
        text = response.json()["choices"][0]["message"]["content"]
        if response_format:
            text = text.split("```json")[1].split("```")[0].strip()
            text = json.loads(text)
        print(text)
    else:
        print(f"Error: {response.status_code} - {response.text}")


def chat_gemini(prompt, model="gemini-2.5-pro", location="europe-west1"):
    # Auth
    file_path = os.path.join(os.path.dirname(__file__), "..", "google.json")
    creds = service_account.Credentials.from_service_account_file(file_path, scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(Request())

    # API Call
    response = requests.post(
        f"https://{location}-aiplatform.googleapis.com/v1/projects/zalazium-gmbh/locations/{location}/publishers/google/models/{model}:generateContent",
        headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
        json={"contents": [{"role": "user", "parts": [{"text": prompt}]}]},
    )

    try:
        data = response.json()
        print(data["candidates"][0]["content"]["parts"][0]["text"])
    except:
        print(f"Fehler: {response.status_code} - {response.text}")


def image_gemini(prompt, model="imagen-3.0-generate-002", location="europe-west1", number_of_images=1, aspect_ratio="1:1"):
    # Auth
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
            "negativePrompt": "",
            "personGeneration": "allow_all",
            "safetyFilterLevel": "block_few",
            "addWatermark": True,
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
                    file = os.path.join(DATA_DIR, f"image.png" if i == 0 else f"image_{i}.png")
                    print(f"Image saved: {file}")
                    with open(file, "wb") as f:
                        f.write(image_data)
        else:
            print(f"Unerwartete Antwort: {data}")
    except Exception as e:
        print(f"Fehler: {response.status_code} - {response.text}")
        print(f"Exception: {e}")


def transcribe_azure(file="30sec.mp3"):
    file = os.path.join(DATA_DIR, file)
    with open(file, "rb") as audio_file:
        files = {"file": (os.path.basename(file), audio_file, "audio/mpeg")}
        response = requests.post(os.getenv("AZURE_OPENAI_ENDPOINT_WHISPER"), headers={"api-key": os.getenv("AZURE_API_KEY_WHISPER")}, files=files)
        if response.status_code == 200:
            result = response.json()
            print(result.get("text", "Kein Text in der Antwort gefunden."))
        else:
            print(f"error: {response.status_code} - {response.text}")


def transcribe_litellm(file="30sec.mp3"):
    file = os.path.join(DATA_DIR, file)
    endpoint_url = os.getenv("LITELLM_URL") + "/v1/audio/transcriptions"
    with open(file, "rb") as audio_file:
        files = {"file": (os.path.basename(file), audio_file, "audio/mpeg")}
        headers = {"Authorization": f"Bearer {os.getenv("LITELLM_MASTER_KEY")}"}
        data = {"model": "azure-whisper", "duration": 6500000, "usage": {"duration_seconds": 6500000, "duration": 6500000}}
        response = requests.post(endpoint_url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            print(response.json().get("text", "Kein Text in der Antwort gefunden."))
        else:
            print(f"error: {response.status_code} - {response.text}")


def image_azure(prompt):
    headers = {"api-key": os.getenv("AZURE_API_KEY_IMAGE"), "Content-Type": "application/json"}
    data = {"prompt": prompt, "n": 1, "size": "1024x1024"}
    try:
        response = requests.post(os.getenv("AZURE_OPENAI_ENDPOINT_IMAGE"), headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        # URL des generierten Bildes auslesen
        image_url = result["data"][0].get("url")
        if image_url:
            file = os.path.join(DATA_DIR, "image.png")
            print(f"Image saved: {file}")
            with open(file, "wb") as f:
                f.write(requests.get(image_url).content)
        else:
            print("Keine Bild-URL in der Antwort enthalten.")
    except requests.exceptions.RequestException as e:
        print(f"Fehler bei der Anfrage: {e}")
    except (KeyError, IndexError):
        print("Antwortstruktur war unerwartet oder leer.")


def image_litellm(prompt, model="dall-e-3"):
    url = os.getenv("LITELLM_URL") + "/v1/images/generations"
    headers = {"Authorization": f"Bearer {os.getenv('LITELLM_MASTER_KEY')}", "Content-Type": "application/json"}
    data = {"model": model, "prompt": prompt, "n": 1, "size": "1024x1024"}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        image_url = result["data"][0].get("url")
        if image_url:
            file = os.path.join(DATA_DIR, "image.png")
            print(f"Image saved: {file}")
            with open(file, "wb") as f:
                f.write(requests.get(image_url).content)
        else:
            print("Keine Bild-URL in der LiteLLM-Antwort enthalten.")
    except requests.exceptions.RequestException as e:
        print(f"Fehler bei der LiteLLM-Anfrage: {e}")
    except (KeyError, IndexError):
        print("Antwortstruktur war unerwartet oder leer.")


if __name__ == "__main__":
    t0 = time.time()
    os.system("clear")

    model = "azure-gpt-4o"
    prompt = "Wie schwer ist die Sonne? Antworte in max. 10 Wörtern."
    key = "sk-_J1iC-d6MUXx8Il6Bia6_w"
    endpoint_url = "https://prd.billing.zalazium.de/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(endpoint_url, headers=headers, json=data)
    text = response.json()["choices"][0]["message"]["content"]
    print(text)

    location = "europe-west1"  # belgium

    # chat_gemini(prompt="Wie schwer ist die Sonne? Antworte in max. 10 Wörtern.", model="gemini-2.5-flash", location=location)
    # chat_litellm(prompt="Wie schwer ist die Sonne?")
    # chat_litellm(prompt="Rechnung vom 21.12.2025, 35 €.", response_format={"Datum": "extrahiere das Datum im YYY.MM.DD Format", "Betrag": "Float mit 2 Nachkommastellen"})
    # image_gemini(prompt="Biene mit blauem Hut!")
    # chat_litellm(prompt="Wie schwer ist die Sonne?")
    # transcribe_azure(file="1min.mp3")
    # transcribe_litellm(file="1min.mp3")
    # image_azure(prompt="Bild von einem Esel")
    # image_litellm(prompt="Bild von einem Esel")

    print(f"Time elapsed: {time.time() - t0:.1f} s")
