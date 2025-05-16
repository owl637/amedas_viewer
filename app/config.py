# config.py
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  # Flask起動ディレクトリ

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CSV_CACHE_PATH = os.path.join(DATA_DIR, "latest.csv")
