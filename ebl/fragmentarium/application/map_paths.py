from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MAP_SOURCE_DIR = REPOSITORY_ROOT / "Maps"
MAP_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "map"
