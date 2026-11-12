
from pathlib import Path

# Racine du projet : ProjetLinux/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Répertoires des ressources
ASSETS_DIR = PROJECT_ROOT / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
ICONS_DIR = ASSETS_DIR / "icones"

# Fichier de rapport
CSV_PATH = PROJECT_ROOT / "data_export.csv"
