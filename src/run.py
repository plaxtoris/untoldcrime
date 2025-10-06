from config import DATA_DIR
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
from generator import generate
from itertools import product
from mutagen.mp3 import MP3
from pathlib import Path
from tqdm import tqdm
import shutil
import time
import os


def clean_data():
    mp3_files = Path(DATA_DIR).rglob("*.mp3")
    total_duration = 0
    for mp3_file in sorted(mp3_files):
        audio = MP3(mp3_file)
        duration_min = audio.info.length / 60
        if (duration_min < 10) or (duration_min > 45):
            rel_path = mp3_file.relative_to(DATA_DIR)
            print(f"{rel_path}: {duration_min:.2f} min")
            shutil.rmtree(mp3_file.parent)
        else:
            total_duration += duration_min

    print(f"\nTotal: {total_duration/60:.1f} h")


def count_data():
    mp3_counts = Counter(p.parent.relative_to(DATA_DIR) for p in Path(DATA_DIR).rglob("*.mp3"))
    for subdir, count in sorted(mp3_counts.items()):
        print(f"{str(subdir):<20} {count} files")


if __name__ == "__main__":
    t0 = time.time()
    os.system("clear")

    # model = "azure-gpt-4.1"
    model = "gemini-2.5-pro"
    generate(model=model, word_limit=1000, setting="Narzisten mit Borderline wird mit freund schwanger...")

    # count_data()
    # clean_data()
    print(f"\n>>> runtime {(time.time() - t0):.1f} sec\n\n")
