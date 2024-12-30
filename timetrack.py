#!/usr/bin/env python3

import sqlite3
import uuid
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List

TIMETRACK_DB = "timetrack.db"
STATUSBAR_FILE = "/tmp/task"
CURRENT_WEEK_DIR = Path("/tmp")


def adapt_datetime_epoch(val):
    """Adapt datetime.datetime to Unix timestamp."""
    return int(val.timestamp())


sqlite3.register_adapter(datetime, adapt_datetime_epoch)


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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS last_logged (
        uuid TEXT PRIMARY KEY
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
        print("There's currently a task running!")
        return

    uuid = get_short_uuid()
    task_data = {
        "uuid": uuid,
        "start_time": datetime.now().timestamp(),
        "end_time": None,
        "name": name,
        "is_logged": False,
    }
    add_task(cursor, task_data)
    print(f"Started task with UUID {uuid}.")


def stop_task(cursor):
    if not is_task_running(cursor):
        print("No task currently running!")
        return
    cursor.execute("""
    SELECT * FROM tasks
    ORDER BY start_time DESC
    LIMIT 1
    """)

    task = cursor.fetchone()
    uuid = task[0]

    cursor.execute(
        """
    UPDATE tasks
    SET end_time = ?
    WHERE uuid = ?
    """,
        (datetime.now().timestamp(), uuid),
    )
    start_time = datetime.fromtimestamp(task[1])
    diff_mins = int(
        ((datetime.now() - start_time).total_seconds() %
         3600) // 60)
    print(f"Ended task {uuid} (ran for {diff_mins} mins).")


def show_task(cursor, uuid, showDate=False, showWeekDay=True):
    cursor.execute(
        """
            SELECT * FROM tasks
            WHERE uuid = ?;
            """,
        (uuid,),
    )
    task = cursor.fetchone()
    if showDate:
        start_time = datetime.fromtimestamp(
            task[1]).strftime("%a %-d.%-m.: %-H:%M")
    elif showWeekDay:
        start_time = datetime.fromtimestamp(task[1]).strftime("%a: %-H:%M")
    else:
        start_time = datetime.fromtimestamp(task[1]).strftime("%-H:%M")

    if task[2]:
        end_time = datetime.fromtimestamp(task[2]).strftime(" - %-H:%M")
    else:
        end_time = " - ?"
    print(start_time + end_time + f", {task[3]}")


def get_unlogged_task_uuids(cursor):
    cursor.execute(
        """
            SELECT * FROM tasks
            WHERE is_logged IS FALSE
            """
    )

    unloggedTaskUUIDs = [task[0] for task in cursor.fetchall() if task[4] != 1]
    return unloggedTaskUUIDs


def show_unlogged_tasks(cursor):
    print("Unlogged tasks:")
    unloggedTaskUUIDs = get_unlogged_task_uuids(cursor)
    if not unloggedTaskUUIDs:
        print("No unlogged tasks found.")
        return
    for uuid in unloggedTaskUUIDs:
        show_task(cursor, uuid, showDate=True)


def show_all_tasks(cursor):
    print("All recorded tasks:")
    cursor.execute(
        """
            SELECT * FROM tasks
            """
    )
    tasks = cursor.fetchall()
    for task in tasks:
        show_task(cursor, task[0], showDate=True)


def unlog_tasks(cursor):
    cursor.execute("""
                   SELECT * FROM last_logged
                   """)
    lastLoggedUUIDs = [x[0] for x in cursor.fetchall()]
    if not lastLoggedUUIDs:
        print("No history of logging found - only one undo level is supported.")
        return
    print(f"Reset the following tasks' log status:")
    for uuid in lastLoggedUUIDs:
        cursor.execute(
            """
        UPDATE tasks
        SET is_logged = ?
        WHERE uuid = ?
        """,
            (False, uuid),
        )
        cursor.execute(
            """
                SELECT * FROM tasks
                WHERE uuid = ?
                """, (uuid,)
        )
        task = cursor.fetchone()
        print(f"{task[0]}: {task[3]}")
    cursor.execute(
        """
            DELETE FROM last_logged;
            """
    )


def log_tasks(cursor):
    unloggedTaskUUIDs = get_unlogged_task_uuids(cursor)
    if not unloggedTaskUUIDs:
        print("No unlogged tasks found.")
        return
    print("Marked the following tasks as logged:")
    cursor.execute(
        """
            DELETE FROM last_logged;
            """
    )
    for uuid in unloggedTaskUUIDs:
        cursor.execute(
            """
        UPDATE tasks
        SET is_logged = ?
        WHERE uuid = ?
        """,
            (True, uuid),
        )
        show_task(cursor, uuid)
        cursor.execute(
            """
                INSERT INTO last_logged
                VALUES (?)
                """,
            (uuid,)
        )


def show_db(cursor):
    print("\n\n----------------------- Debug output:")
    cursor.execute("SELECT * FROM tasks")
    for row in cursor.fetchall():
        print(row)
    print("\n\n----------------------- Last logged:")
    cursor.execute("SELECT * FROM last_logged")
    for row in cursor.fetchall():
        print(row)


def show_today_tasks(cursor):
    today = datetime.today().date()
    print(today.strftime("Tasks on %a, %-d.%-m.:"))
    cursor.execute(
        """
            SELECT * FROM tasks
            """
    )
    tasks = cursor.fetchall()
    todayTaskUUIDs = [
        x[0] for x in tasks if datetime.fromtimestamp(x[1]).date() == today
    ]
    for uuid in todayTaskUUIDs:
        show_task(cursor, uuid, showWeekDay=False)


def get_this_week_uuids(cursor):
    this_week = datetime.today().date().isocalendar()[1]
    this_year = datetime.today().date().isocalendar()[0]
    cursor.execute(
        """
            SELECT * FROM tasks
            """
    )
    tasks = cursor.fetchall()
    thisWeekUUIDs = [
        x[0]
        for x in tasks
        if datetime.fromtimestamp(x[1]).date().isocalendar()[1] == this_week
        and datetime.fromtimestamp(x[1]).date().isocalendar()[0] == this_year
    ]
    return thisWeekUUIDs


def get_task_length_in_mins(cursor, uuid):
    cursor.execute("SELECT * FROM tasks WHERE uuid = ?", (uuid,))
    task = cursor.fetchone()
    if not task[2]:
        return 0
    return int((task[2] - task[1]) / 60)


def get_task_lengths_in_mins(cursor, uuids: List[str]):
    total_mins = 0
    for uuid in uuids:
        total_mins += get_task_length_in_mins(cursor, uuid)
    return total_mins


def show_this_week_tasks(cursor):
    thisWeekUUIDs = get_this_week_uuids(cursor)
    if not thisWeekUUIDs:
        print("No tasks yet this week.")
        return
    this_week = datetime.today().date().isocalendar()[1]
    this_year = datetime.today().date().isocalendar()[0]
    total_mins = get_task_lengths_in_mins(cursor, thisWeekUUIDs)
    hours = total_mins // 60
    mins = total_mins % 60
    print(f"Tasks in KW {this_week}/{this_year} ({hours}:{mins} so far):")
    for uuid in thisWeekUUIDs:
        show_task(cursor, uuid, showWeekDay=True)


def add_example_task(cursor):
    task_data = {
        "uuid": get_short_uuid(),
        "start_time": datetime.now().timestamp(),
        "end_time": datetime.now().timestamp(),
        "name": "My Task",
        "is_logged": False,
    }

    add_task(cursor, task_data)


def update_statusbar(cursor):
    with open(STATUSBAR_FILE, "w") as f:
        f.write("Hä?")  # TODO


def show_status(cursor):
    if not is_task_running(cursor):
        print("No task currently running!")
        return
    cursor.execute("""
    SELECT * FROM tasks
    ORDER BY start_time DESC
    LIMIT 1
    """)

    task = cursor.fetchone()
    start_time = datetime.fromtimestamp(task[1])
    diff_mins = int(
        ((datetime.now() - start_time).total_seconds() %
         3600) // 60)
    start_time = start_time.strftime("%-H:%M")
    print(
        f'Task "{
            task[3]}" with UUID {
            task[0]} is running since {start_time} ({diff_mins} mins).'
    )


def main():
    parser = argparse.ArgumentParser(description="Time logging tool")

    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start a task")
    start_parser.add_argument("task_name", help="Name of the task")
    show_parser = subparsers.add_parser("show", help="Show past tasks")
    show_parser.add_argument(
        "filter",
        help="Which tasks to show",
        choices=["all", "week", "today", "unlogged"],
    )
    subparsers.add_parser("log", help="Mark all tasks as logged")
    subparsers.add_parser(
        "unlog",
        help="Undo the last operation that marked tasks logged.")
    subparsers.add_parser(
        "status",
        help="Show info about currently running task")
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
                show_status(cursor)
            case "unlog":
                unlog_tasks(cursor)
            case "log":
                log_tasks(cursor)
            case "show":
                match args.filter:
                    case "week":
                        show_this_week_tasks(cursor)
                    case "today":
                        show_today_tasks(cursor)
                    case "unlogged":
                        show_unlogged_tasks(cursor)
                    case "all":
                        show_all_tasks(cursor)
            case _:
                raise ValueError

    show_db(cursor)
    update_statusbar(cursor)


if __name__ == "__main__":
    main()
