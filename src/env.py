from dotenv import load_dotenv
from pathlib import Path
import os

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

TIMETRACK_DB = os.getenv("TIMETRACK_DB", "/tmp/timetrack.db")
TASK_ID = os.getenv("TASK_ID", "1")
PROJECT_ID = os.getenv("TASK_ID", "1")
ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", "/tmp/archive"))
STATUSBAR_FILE = Path(os.getenv("STATUSBAR_FILE", "/tmp/task"))

EMAIL = os.getenv("EMAIL")
HARVEST_TOKEN = os.getenv("HARVEST_TOKEN")
HARVEST_ACCOUNT_ID = os.getenv("HARVEST_ACCOUNT_ID")
HOURS = os.getenv("HOURS")
