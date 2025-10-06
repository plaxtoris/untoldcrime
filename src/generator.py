from config import DATA_DIR
from cover import cover
from llm import prompt
from tts import speak
import secrets
import os


def generate(model="azure-gpt-4.1", word_limit=100, setting="Bitcoin Darknet"):
    # story
    output = prompt(model=model, word_limit=word_limit, setting=setting)

    # path
    dir = os.path.join(DATA_DIR, secrets.token_hex(8))
    os.makedirs(dir, exist_ok=True)
    filepath = os.path.join(dir, f"{output['title']}.wav")

    # cover
    cover(topic=output["summary"], dir=dir)

    # audio
    speak(text=output["story"], filepath=filepath)
    return output
