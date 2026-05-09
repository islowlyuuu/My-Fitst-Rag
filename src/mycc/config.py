"""Configuration management."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
NOTES_DIR = ROOT_DIR / "notes"
DATA_DIR = ROOT_DIR / "data"
LANCEDB_PATH = DATA_DIR / "lancedb"
INDEX_META_PATH = DATA_DIR / "index_meta.json"

EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
EMBEDDING_DEVICE = "cpu"
TOP_K_DEFAULT = 5
TABLE_NAME = "chunks"
