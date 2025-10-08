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
    "Der letzte Stream: Eine erfolgreiche Influencerin aus Hamburg wird live während ihres Streams bewusstlos – die Kamera läuft weiter. Tausende Follower sind Zeugen, doch niemand weiß: War es ein medizinischer Notfall oder inszenierter Mord vor laufender Kamera?",
    "Kaltblütig kalkuliert: Ein Investmentbanker verschwindet spurlos aus seinem Büro im Frankfurter Bankenviertel. Seine Kollegin entdeckt, dass er Milliarden in Kryptowährungen verschoben hat – war es Flucht oder wurde er eliminiert, bevor er auspacken konnte?",
    "Tod auf der Wiesn: Während des Oktoberfests stirbt ein Festzelt-Wirt unter mysteriösen Umständen. Die Ermittlungen fördern einen erbitterten Kampf um die lukrativen Standplätze und eine jahrzehntealte Familienfehde zutage.",
    "Der Schatten der Vergangenheit: In Dresden wird die Leiche eines pensionierten Lehrers gefunden – mit Stasi-Akten in seiner Hand. Ein investigativer Journalist deckt auf, dass mehrere seiner ehemaligen Kollegen ebenfalls verschwunden sind.",
    "Blutige Pisten: Ein russischer Oligarch verunglückt tödlich beim Après-Ski in Garmisch. Sein Bodyguard behauptet, es war Mord. Die Ermittlungen enthüllen ein Netzwerk aus Geldwäsche, gestohlenen Kunstschätzen und Geheimdiensten.",
    "Dark Web Roulette: Ein Programmierer aus Leipzig wird tot aufgefunden, sein Laptop verschlüsselt. Die Cyber-Kripo entdeckt, dass er Zugang zu einem illegalen Dark-Web-Marktplatz hatte – und zu viel über die Betreiber wusste.",
    "Die Schattenseite des Erfolgs: Eine gefeierte Fernsehmoderatorin stürzt von ihrem Balkon in Potsdam. Selbstmord wegen Burn-out? Doch ihre Assistentin findet Beweise für systematisches Stalking und einen obsessiven Fan.",
    "Tödliche Diagnose: In einer Hamburger Privatklinik sterben innerhalb von Wochen drei Patienten an 'Komplikationen'. Eine Krankenschwester wird misstrauisch und stößt auf einen Organhandel-Ring mit Verbindungen bis in die Klinikleitung.",
    "Der Flüsterer von Sylt: Ein Immobilienmakler, der die Superreichen der Insel berät, wird ermordet aufgefunden. Seine verschlüsselten Notizen offenbaren Erpressungen, illegale Bauvorhaben und dunkle Geheimnisse der Elite.",
    "Autobahnmord A9: Ein Fernfahrer findet eine Leiche im Container seines LKW. Die Spurensuche führt quer durch Deutschland und deckt einen internationalen Menschenhandel-Ring auf, der die Autobahnen als unsichtbare Routen nutzt.",
    "Tod im Yoga-Retreat: Eine Wellness-Influencerin stirbt während eines teuren Detox-Retreats in den bayerischen Alpen. Die Polizei vermutet vergiftete Kräuter, doch die Wahrheit liegt in ihrer verschwiegenen Vergangenheit als Pharma-Whistleblowerin.",
    "Der Algorithmus des Todes: Ein KI-Forscher in München wird tot in seinem Labor gefunden. Seine letzte Entwicklung: ein Algorithmus, der angeblich Verbrechen vorhersagen kann. Hat seine KI seinen eigenen Mord vorhergesagt?",
    "Blutgeld im Kleingartenverein: In einer Stuttgarter Schrebergartenkolonie wird ein beliebter Vereinsvorsitzender erschlagen. Die idyllische Fassade bröckelt: Drogenanbau, illegales Glücksspiel und ein Netz aus Lügen kommen ans Licht.",
    "Die Rache der Ghostwriterin: Eine erfolgreiche Bestseller-Autorin stirbt bei einem inszenierten Autounfall. Ihre unbekannte Ghostwriterin wird zur Hauptverdächtigen – doch hat sie wirklich gemordet oder deckt sie einen literarischen Betrug auf?",
    "Todesfall Pflegeheim: In einem Nürnberger Seniorenheim häufen sich mysteriöse Todesfälle. Eine neue Pflegekraft deckt auf, dass Angehörige die Erbschaften beschleunigen wollten – mit tödlicher Hilfe eines korrupten Arztes.",
    "Der Skandal von St. Pauli: Ein Nachtclub-Besitzer wird auf der Reeperbahn exekutiert. Die Ermittlungen offenbaren einen Machtkampf zwischen rivalisierenden Clans, die um die Kontrolle des Rotlichtmilieus kämpfen.",
    "Mord im Escape Room: Eine Gruppe Studenten spielt in einem Kölner Escape Room – einer von ihnen überlebt nicht. War es ein tragischer Unfall oder hat jemand das Spiel in eine tödliche Falle verwandelt? Die Überwachungskameras wurden manipuliert.",
    "Der Fall des Flüchtlingshelfers: Ein engagierter Sozialarbeiter in Berlin wird ermordet. Hat er zu viel über die Machenschaften in einem Asylheim erfahren? Die Spur führt zu korrupten Behörden und organisierten Schlepperbanden.",
    "Tödliche Likes: Ein aufstrebender TikToker aus Düsseldorf stirbt bei einem waghalsigen Stunt. Zufall oder wurde er von einem eifersüchtigen Konkurrenten manipuliert? Die digitale Forensik enthüllt einen Psychokrieg in den sozialen Medien.",
    "Das Vermächtnis des Winzers: Auf einem renommierten Weingut an der Mosel wird der Besitzer tot in seinem Weinkeller gefunden. Seine drei Kinder kämpfen ums Erbe – doch einer von ihnen hat ein tödliches Geheimnis zu verbergen.",
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
