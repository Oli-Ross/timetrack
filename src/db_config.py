from peewee import SqliteDatabase
from pathlib import Path
from env import TIMETRACK_DB

db = SqliteDatabase(TIMETRACK_DB)
