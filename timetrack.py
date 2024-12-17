import sqlite3
import uuid
import argparse
from datetime import datetime
from typing import Dict

TIMETRACK_DB = "timetrack.db"
STATUSBAR_FILE = "/tmp/task"


def get_short_uuid():
    return str(uuid.uuid4())[:8]


def setup(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        uuid TEXT PRIMARY KEY,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        name TEXT,
        is_logged BOOLEAN
    )
    """)
    return cursor


def add_task(cursor, task_data: Dict[str, str | datetime | bool | None]):
    cursor.execute(
        """
    INSERT INTO tasks (uuid, start_time, end_time, name, is_logged) 
    VALUES (:uuid, :start_time, :end_time, :name, :is_logged)
    """,
        task_data,
    )


def is_task_running(cursor):
    cursor.execute(
        """
    SELECT * FROM tasks 
    WHERE end_time IS NULL
    """
    )

    return cursor.fetchall() != []


def start_task(cursor, name: str):
    if is_task_running(cursor):
        raise ValueError("There's currently a task running!")

    task_data = {
        "uuid": get_short_uuid(),
        "start_time": datetime.now(),
        "end_time": None,
        "name": name,
        "is_logged": False,
    }
    add_task(cursor, task_data)


def stop_task(cursor):
    if not is_task_running(cursor):
        raise ValueError("No task currently running!")
    cursor.execute("""
    SELECT uuid FROM tasks 
    ORDER BY start_time DESC 
    LIMIT 1
    """)

    uuid = cursor.fetchone()[0]

    cursor.execute(
        """
    UPDATE tasks
    SET end_time = ? 
    WHERE uuid = ?
    """,
        (datetime.now(), uuid),
    )


def show_db(cursor):
    cursor.execute("SELECT * FROM tasks")
    for row in cursor.fetchall():
        print(row)


def add_example_task(cursor):
    task_data = {
        "uuid": get_short_uuid(),
        "start_time": datetime.now(),
        "end_time": datetime.now(),
        "name": "My Task",
        "is_logged": False,
    }

    add_task(cursor, task_data)


def update_statusbar(cursor):
    with open(STATUSBAR_FILE, "w") as f:
        f.write("Hä?")  # TODO


def main():
    parser = argparse.ArgumentParser(description="Time logging tool")

    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start a task")
    start_parser.add_argument("task_name", help="Name of the task")
    show_parser = subparsers.add_parser("show", help="Show past tasks")
    show_parser.add_argument(
        "filter", help="Which tasks to show", choices=["week", "day", "unlogged"]
    )
    subparsers.add_parser("log", help="Mark all tasks as logged")
    subparsers.add_parser("stop", help="Stop current task")

    args = parser.parse_args()

    with sqlite3.connect(TIMETRACK_DB, isolation_level=None) as connection:
        cursor = setup(connection.cursor())
        match args.command:
            case "start":
                start_task(cursor, args.task_name)
            case "stop":
                stop_task(cursor)
            case "status":
                raise NotImplementedError
            case "log":
                raise NotImplementedError
            case "show":
                raise NotImplementedError
            case _:
                raise ValueError

    show_db(cursor)
    update_statusbar(cursor)


if __name__ == "__main__":
    main()
