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
    settings = [
        "Bitcoin-Mining auf Teneriffa, russische Mafia bekommt Wind davon",
        "Kunstfälscher-Ring in München, gefälschte Expressionisten im Auktionshaus",
        "Darknet-Drogenhandel über Paketshops in Nordrhein-Westfalen, verdeckte Ermittler",
        "Identitätsdiebstahl in Berliner Startup-Szene, Investor verliert Millionen",
        "Illegales Online-Casino in Frankfurt, Geldwäsche über Scheinfirmen",
        "Hackerangriff auf mittelständisches Unternehmen in Stuttgart, Ransomware-Erpressung",
        "Pflegeheim-Betrug in Hamburg, systematische Abrechnungsmanipulation",
        "NFT-Scam mit gefälschten digitalen Kunstwerken, Opfer in ganz Deutschland",
        "Einbruchserie in Villenviertel am Starnberger See, Insider-Wissen vermutet",
        "Kryptowährungs-Ponzi-Scheme in Leipzig, vermeintlicher Finanz-Guru",
        "Autodiebstahl-Ring an deutsch-polnischer Grenze, GPS-Tracker ausgetrickst",
        "Social-Engineering-Betrug bei Seniorin in Köln, Enkeltrick 2.0",
        "Unterschlagung in kommunaler Verwaltung Niedersachsen, jahrelange Manipulationen",
        "Darknet-Waffenhandel vom Kinderzimmer aus, 17-jähriger Schüler als Händler",
        "Phishing-Kampagne gegen Online-Banking-Kunden, Server in Osteuropa",
        "Betrug mit gefälschten Impfzertifikaten während Pandemie, bundesweites Netzwerk",
        "Insider-Trading bei Pharmaunternehmen in Basel, vertrauliche Studiendaten",
        "Koks-Schmuggel im Containerhafen Hamburg, korrupter Zollbeamter",
        "Betrügerische Pflegedienst-Abrechnung in Brandenburg, fiktive Patienten",
        "CEO-Fraud bei Mittelständler in Baden-Württemberg, gefälschte E-Mail kostet 2 Millionen",
    ]
    for setting in tqdm(settings, desc="Generating stories"):
        generate(model="gemini-2.5-pro", word_limit=75000, setting=setting)

    # count_data()
    clean_data()
    print(f"\n>>> runtime {(time.time() - t0):.1f} sec\n\n")
