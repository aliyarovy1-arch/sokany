from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
CHANNEL = os.environ["TELEGRAM_CHANNEL"]
SA_PATH = Path(os.environ["GOOGLE_SA_PATH"])
SHEET_NAME = os.environ["GOOGLE_SHEET_NAME"]
DB_PATH = Path(os.environ.get("DB_PATH", "data/sokany.db"))
IMGBB_API_KEY = os.environ["IMGBB_API_KEY"]
