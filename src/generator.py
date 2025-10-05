from helper import DATA_DIR
from llm import prompt
from tts import speak
import os


def generate(model="azure-gpt-4.1", theme="Piraten", word_limit=100, target_group="Kinder von 6 Jahren bis 14 Jahren"):
    # story
    output = prompt(model=model, theme=theme, word_limit=word_limit, target_group=target_group)

    # path
    theme_dir = os.path.join(DATA_DIR, theme)
    os.makedirs(theme_dir, exist_ok=True)
    filepath = os.path.join(theme_dir, f"{output['title']}.wav")

    # audio
    speak(text=output["story"], filepath=filepath)
    return output
