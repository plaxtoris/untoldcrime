"""Batch story generation and data management utilities."""

from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import Counter
from pathlib import Path
from mutagen.mp3 import MP3
from tqdm import tqdm
from config import DATA_DIR, MIN_STORY_DURATION_MIN, MAX_STORY_DURATION_MIN, DEFAULT_MODEL, DEFAULT_WORD_LIMIT
from generator import generate_complete_story
from utils import format_time_seconds
import shutil
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


STORY_SETTINGS = [
    # Digitale Abgründe & Moderne Verbrechen
    "Mord im Smart Home: Ein Tech-Mogul stirbt in seiner vollautomatisierten Villa in Grünwald. Die Polizei vermutet einen Unfall, doch eine IT-Forensikerin entdeckt, dass das Haus selbst zur Tatwaffe umprogrammiert wurde.",
    "Rache für die Oma: Nachdem ihre Großmutter von einem 'Love Scammer' ausgenommen wird, nutzt eine junge Datenanalystin ihre Fähigkeiten, um den Betrüger digital zu jagen – und stößt auf ein internationales Geldwäsche-Netzwerk.",
    "Game Over in Köln: Ein E-Sport-Profi stirbt vor einem wichtigen Finale an einer Überdosis Aufputschmittel. Sein größter Rivale gerät in Verdacht, doch die Spur führt zu einem Wettsyndikat, das Matches manipuliert.",
    # Gesellschaftliche Risse & Subkulturen
    "Tod im Bunker: Der Anführer einer Prepper-Gruppe in der Eifel wird tot in seinem unterirdischen Versteck gefunden. Die Ermittler tauchen ein in eine Welt aus Paranoia, Verschwörungstheorien und internen Machtkämpfen.",
    "Burnout oder Mord? Der verdächtige Suizid eines Entwicklers in der Berliner Startup-Szene. Ein Whistleblower behauptet, der gefeierte CEO habe ihn durch toxische 'Hustle Culture' in den Tod getrieben.",
    "Radikaler Umweltschutz mit Todesfolge: Ein Aktivist, der eine Firma in der Lausitz sabotiert hat, wird ermordet. War es die Rache des Konzerns oder ein interner Konflikt in der eskalierenden Bewegung?",
    # Psychologische Twists & Familiendramen
    "Tödliche Erleuchtung: Ein Mitglied eines exklusiven Selbsthilfe-Kults stirbt bei einem Ritual in einer Villa im Taunus. Während die Anhänger von einem Unfall sprechen, schleust die Familie des Opfers einen Privatdetektiv in die sektenartige Gemeinschaft ein.",
    "Die falsche Schwester: Jahrzehnte nach einer Entführung taucht eine Frau auf, die per DNA-Test als die vermisste Schwester identifiziert wird. Doch ein misstrauischer Bruder deckt auf, dass die 'Heimkehrerin' eine Betrügerin mit einem tödlichen Plan ist.",
    # Klassische Verbrechen im neuen Gewand
    "Das gefälschte Meisterwerk: Ein renommierter Kunstexperte wird in München ermordet, kurz nachdem er ein wiederentdecktes Gemälde als Sensation gefeiert hat. Die Ermittlungen enthüllen einen Fälscherring in den höchsten Kreisen des Kunstmarktes.",
    "Der Fluch des Lottogewinns: Eine Tippgemeinschaft aus einem Dorf in Brandenburg gewinnt den Jackpot. Kurz darauf stirbt ein Mitglied nach dem anderen durch seltsame 'Unfälle'. Ein klassischer Fall von Gier – oder steckt mehr dahinter?",
]


def clean_invalid_stories() -> None:
    """Remove stories that don't meet duration requirements or are missing cover images."""
    logger.info("Cleaning invalid stories...")
    mp3_files = list(Path(DATA_DIR).rglob("*.mp3"))
    total_duration = 0.0
    removed_count = 0

    for mp3_file in sorted(mp3_files):
        try:
            audio = MP3(mp3_file)
            duration_min = audio.info.length / 60
            cover_path = mp3_file.parent / "cover.png"

            if duration_min < MIN_STORY_DURATION_MIN or duration_min > MAX_STORY_DURATION_MIN:
                rel_path = mp3_file.relative_to(DATA_DIR)
                logger.info(f"Removing invalid story: {rel_path} ({duration_min:.2f} min)")
                shutil.rmtree(mp3_file.parent)
                removed_count += 1
            elif not cover_path.exists():
                rel_path = mp3_file.relative_to(DATA_DIR)
                logger.info(f"Removing story without cover: {rel_path}")
                shutil.rmtree(mp3_file.parent)
                removed_count += 1
            else:
                total_duration += duration_min

        except Exception as e:
            logger.error(f"Error processing {mp3_file}: {e}")

    total_hours = total_duration / 60
    logger.info(f"Cleanup complete: {removed_count} removed, {total_hours:.1f}h remaining")


def count_stories() -> None:
    """Display total playtime of all stories."""
    mp3_files = list(Path(DATA_DIR).rglob("*.mp3"))
    total_duration = 0.0

    for mp3_file in mp3_files:
        try:
            audio = MP3(mp3_file)
            total_duration += audio.info.length / 60
        except Exception as e:
            logger.error(f"Error processing {mp3_file}: {e}")

    total_hours = total_duration / 60
    logger.info(f"Total playtime: {total_hours:.1f}h ({len(mp3_files)} stories)")


def generate_batch(settings: list[str], model: str = DEFAULT_MODEL, word_limit: int = DEFAULT_WORD_LIMIT, max_workers: int = 3) -> None:
    """Generate multiple stories in parallel.

    Args:
        settings: List of story settings
        model: LLM model to use
        word_limit: Target word count
        max_workers: Number of parallel workers
    """
    logger.info(f"Starting batch generation of {len(settings)} stories")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(generate_complete_story, model=model, word_limit=word_limit, setting=setting): setting for setting in settings}

        for future in tqdm(as_completed(futures), total=len(settings), desc="Generating stories"):
            setting = futures[future]
            try:
                result = future.result()
                if result:
                    logger.info(f"✓ Completed: {setting}")
                else:
                    logger.error(f"✗ Failed: {setting}")
            except Exception as e:
                logger.error(f"✗ Error generating '{setting}': {e}")


def main() -> None:
    """Main entry point for story generation."""
    start_time = time.time()

    # Generate stories
    generate_batch(STORY_SETTINGS, max_workers=5)

    # cleanup
    clean_invalid_stories()
    count_stories()

    elapsed = time.time() - start_time
    logger.info(f"Total runtime: {format_time_seconds(elapsed)}")


if __name__ == "__main__":
    main()
