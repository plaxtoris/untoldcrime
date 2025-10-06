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
    # Psychologische Thriller & Beziehungsdramen
    "Narzisstischer Missbrauch mit fatalem Ende: Eine Frau verschwindet spurlos, ihr 'perfekter' Ehemann gerät ins Visier der Ermittler, die ein Netz aus psychologischer Manipulation aufdecken.",
    "KI-gestütztes Stalking: Ein Tech-Unternehmer nutzt Deepfake-Technologie, um seine Ex-Freundin in den Wahnsinn zu treiben – die Polizei steht vor einem digitalen Phantom [3, 5].",
    "Toxische Freundschaft in einer Yoga-Community in Berlin-Kreuzberg: Ein Todesfall bei einem Retreat wird als Unfall abgetan, doch eine Freundin vermutet Mord aus Neid und Eifersucht.",
    "Münchhausen-by-Proxy-Syndrom: Eine junge Mutter und Influencerin wird gefeiert, während ihr Kind unerklärlich krank ist. Ein Kinderarzt schöpft Verdacht.",
    "Das Doppelleben eines Familienvaters: Nach seinem plötzlichen Tod entdeckt seine Frau, dass er eine zweite Identität und eine andere Familie in einer Parallelwelt hatte.",
    # High-Tech & Mystery
    "Der 'Hypnose-Bankraub': Eine Serie von Überfällen in Hannover, bei denen die Angestellten den Tätern freiwillig helfen. Die einzige Spur ist ein mysteriöser Psychologe.",
    "Bitcoin-Erpressung mit geklonter Stimme: Ein Manager überweist Millionen, nachdem er einen Anruf von seiner vermeintlich entführten Tochter erhält, deren Stimme per KI geklont wurde [4].",
    "Verschwunden im digitalen Nichts: Ein Journalist, der zu Betrugsmaschen mit KI-Handelsplattformen recherchiert, löst sich online auf – alle seine Profile und Daten sind gelöscht [3].",
    "Kindheitstrauma als Auslöser: Eine Reihe von Sabotageakten in einem Nobel-Internat am Chiemsee führt zu einem Verbrechen, das 20 Jahre zurückliegt.",
    "Die 'prophetische' Künstlerin: Eine Malerin mit diagnostizierter Schizophrenie malt Verbrechen, bevor sie geschehen. Ist sie Medium oder Täterin?",
    # Urban Crime & Gesellschaft
    "Tödliche Gentrifizierung in Hamburg-Ottensen: Ein Bauprojekt wird zum Schauplatz eines Mordes. Die Verdächtigen reichen von verdrängten Mietern bis zu skrupellosen Investoren.",
    "Escort-Mord auf dem Hamburger Kiez: Der Tod einer Edelprostituierten enthüllt die geheimen Verstrickungen von Politik und Wirtschaft im Rotlichtmilieu.",
    "Social-Media-Challenge mit Todesfolge: Ein Jugendlicher stirbt bei einer riskanten 'Mutprobe'. Die Ermittlungen decken auf, dass ein anonymer 'Meister' die Jugendlichen online manipuliert.",
    "Der 'saubere' Drogenring: Designer-Drogen werden über eine Kette von exklusiven Fitnessstudios in Düsseldorf vertrieben. Die Ermittler stoßen auf eine Mauer des Schweigens.",
    "Betrug im Food-Blogger-Milieu: Ein aufstrebender Koch in Leipzig deckt auf, dass ein berühmter Restaurantkritiker Bewertungen verkauft – und wird daraufhin massiv bedroht.",
    # Unglaubliche Wendungen & Twists
    "Der falsche Zeuge: Ein Mann wird für einen Mord verurteilt, den er live im Fernsehen gesehen haben will. Jahre später beweist ein Podcast, dass seine Erinnerung eine Fälschung war.",
    "Das vererbte Verbrechen: Eine junge Frau erbt ein abgeschiedenes Haus im Harz und findet das Tagebuch ihrer Großmutter, das ein ungelöstes Verbrechen aus den 70ern beschreibt – mit erschreckenden Parallelen zur Gegenwart.",
    "Gedächtnisverlust nach einem Überfall: Das Opfer kann sich an nichts erinnern, aber sein Unterbewusstsein liefert in Träumen kryptische Hinweise, die zum Täter führen.",
    "Organhandel im Wellness-Hotel: In einem Luxus-Resort an der Ostsee verschwinden Gäste. Eine verdeckte Ermittlerin stößt auf ein perfides medizinisches Netzwerk.",
    "Der inszenierte Absturz: Eine reiche Erbin täuscht ihren eigenen Tod bei einem Segelunfall vor, um unterzutauchen – doch jemand aus ihrem alten Leben spürt sie auf.",
]


def clean_invalid_stories() -> None:
    """Remove stories that don't meet duration requirements."""
    logger.info("Cleaning invalid stories...")
    mp3_files = list(Path(DATA_DIR).rglob("*.mp3"))
    total_duration = 0.0
    removed_count = 0

    for mp3_file in sorted(mp3_files):
        try:
            audio = MP3(mp3_file)
            duration_min = audio.info.length / 60

            if duration_min < MIN_STORY_DURATION_MIN or duration_min > MAX_STORY_DURATION_MIN:
                rel_path = mp3_file.relative_to(DATA_DIR)
                logger.info(f"Removing invalid story: {rel_path} ({duration_min:.2f} min)")
                shutil.rmtree(mp3_file.parent)
                removed_count += 1
            else:
                total_duration += duration_min

        except Exception as e:
            logger.error(f"Error processing {mp3_file}: {e}")

    total_hours = total_duration / 60
    logger.info(f"Cleanup complete: {removed_count} removed, {total_hours:.1f}h remaining")


def count_stories() -> None:
    """Count and display story statistics."""
    mp3_counts = Counter(p.parent.relative_to(DATA_DIR) for p in Path(DATA_DIR).rglob("*.mp3"))

    logger.info("Story counts by directory:")
    for subdir, count in sorted(mp3_counts.items()):
        logger.info(f"  {str(subdir):<20} {count} files")

    logger.info(f"Total stories: {sum(mp3_counts.values())}")


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
    generate_batch(STORY_SETTINGS, max_workers=3)

    # Clean up invalid stories
    clean_invalid_stories()

    # Show statistics
    count_stories()

    elapsed = time.time() - start_time
    logger.info(f"Total runtime: {format_time_seconds(elapsed)}")


if __name__ == "__main__":
    main()
