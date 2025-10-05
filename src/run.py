from config import DEFAULT_TARGET_GROUP, DEFAULT_WORD_LIMIT, DEFAULT_MODEL, AVAILABLE_THEMES, DATA_DIR
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
from generator import generate
from itertools import product
from mutagen.mp3 import MP3
from pathlib import Path
from tqdm import tqdm
import time
import os


def clean_data():
    mp3_files = Path(DATA_DIR).rglob("*.mp3")
    total_duration = 0
    for mp3_file in sorted(mp3_files):
        audio = MP3(mp3_file)
        duration_min = audio.info.length / 60
        if duration_min < 6:
            print(f"{rel_path}: {duration_min:.2f} min")
            os.remove(mp3_file)
        else:
            total_duration += duration_min
        rel_path = mp3_file.relative_to(DATA_DIR)
    print(f"\nTotal: {total_duration/60:.1f} h")


def count_data():
    mp3_counts = Counter(p.parent.relative_to(DATA_DIR) for p in Path(DATA_DIR).rglob("*.mp3"))
    for subdir, count in sorted(mp3_counts.items()):
        print(f"{str(subdir):<20} {count} files")


def generate_story(args):
    theme, i = args
    return generate(model=DEFAULT_MODEL, theme=theme, word_limit=DEFAULT_WORD_LIMIT, target_group=DEFAULT_TARGET_GROUP)


if __name__ == "__main__":
    t0 = time.time()
    os.system("clear")

    n = 3
    tasks = list(product(AVAILABLE_THEMES, range(n)))
    with ProcessPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(generate_story, task): task for task in tasks}
        with tqdm(total=len(tasks), desc="Generating stories") as pbar:
            for future in as_completed(futures):
                result = future.result()
                pbar.update(1)
    print(f"\n>>> Completed {len(tasks)} stories")

    count_data()
    clean_data()
    print(f"\n>>> runtime {(time.time() - t0):.1f} sec\n\n")
