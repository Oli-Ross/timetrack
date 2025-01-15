from peewee import SqliteDatabase
from pathlib import Path

db = SqliteDatabase(Path(__file__).parent.parent / "timetrack_for_peewee.db")
