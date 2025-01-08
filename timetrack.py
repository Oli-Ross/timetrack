#!/usr/bin/env python3

import sqlite3
import argparse
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

TIMETRACK_DB = "/tmp/timetrack.db"
STATUSBAR_FILE = "/tmp/task"
ARCHIVE_DIR = Path("/tmp")

PROJECT_ID = 1
TASK_ID = 1


def adapt_datetime_epoch(val):
    """Adapt datetime.datetime to Unix timestamp."""
    return int(val.timestamp())


sqlite3.register_adapter(datetime, adapt_datetime_epoch)


def get_short_uuid():
    import uuid

    return str(uuid.uuid4())[:8]


def setup(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        uuid TEXT PRIMARY KEY,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        name TEXT,
        is_logged BOOLEAN,
        taskId TEXT,
        projectId TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS last_logged (
        uuid TEXT PRIMARY KEY
    )
    """)
    return cursor


def get_this_week_uuids(cursor):
    this_week = datetime.today().date().isocalendar()[1]
    this_year = datetime.today().date().isocalendar()[0]
    tasks = get_all_tasks(cursor)
    thisWeekUUIDs = [
        x[0]
        for x in tasks
        if datetime.fromtimestamp(x[1]).date().isocalendar()[1] == this_week
        and datetime.fromtimestamp(x[1]).date().isocalendar()[0] == this_year
    ]
    return thisWeekUUIDs


def get_all_tasks(cursor) -> List[List[str]]:
    cursor.execute("SELECT * FROM tasks")
    return cursor.fetchall()


def get_task(cursor, uuid) -> List[str]:
    cursor.execute("SELECT * FROM tasks WHERE uuid = ?", (uuid,))
    return cursor.fetchone()


def get_task_length_in_mins(cursor, uuid):
    task = get_task(cursor, uuid)
    if task[2]:
        end_time = task[2]
    else:
        end_time = datetime.now().timestamp()
    return int((float(end_time) - float(task[1])) / 60)


def get_task_lengths_in_mins(cursor, uuids: List[str]):
    total_mins = 0
    for uuid in uuids:
        total_mins += get_task_length_in_mins(cursor, uuid)
    return total_mins


def add_task(cursor, task_data: Dict[str, str | datetime | bool | None]):
    cursor.execute(
        """
    INSERT INTO tasks (uuid, start_time, end_time, name, is_logged, taskId, projectId)
    VALUES (:uuid, :start_time, :end_time, :name, :is_logged, :taskId, :projectId)
    """,
        task_data,
    )


def is_task_running(cursor):
    cursor.execute("SELECT * FROM tasks WHERE end_time IS NULL")
    return cursor.fetchall() != []


def next_task(cursor, name: str):
    if is_task_running(cursor):
        stop_task(cursor)

    uuid = get_short_uuid()
    task_data = {
        "uuid": uuid,
        "start_time": datetime.now().timestamp(),
        "end_time": None,
        "name": name,
        "is_logged": False,
        "taskId": None,
        "projectId": None,
    }
    add_task(cursor, task_data)
    print(f"Started task with UUID {uuid}.")


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
        "taskId": None,
        "projectId": None,
    }
    add_task(cursor, task_data)
    print(f"Started task with UUID {uuid}.")


def extend_task(cursor):
    if is_task_running(cursor):
        print("Task currently running!")
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
        (None, uuid),
    )
    print(f'Set task "{task[3]}" {uuid} to running.')


def rename_task(cursor, task_name):
    cursor.execute("""
    SELECT * FROM tasks
    ORDER BY start_time DESC
    LIMIT 1
    """)

    task = cursor.fetchone()
    uuid = task[0]
    old_name = task[3]

    cursor.execute(
        """
    UPDATE tasks
    SET name = ?
    WHERE uuid = ?
    """,
        (task_name, uuid),
    )
    print(f'Renamed "{old_name}" to "{task_name}"')


def abort_task(cursor):
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
    DELETE FROM tasks
    WHERE uuid = ?
    """,
        (uuid,),
    )
    print(f'Aborted task "{task[3]}".')


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
    diff_mins = int(((datetime.now() - start_time).total_seconds() % 3600) / 60)
    print(f"Ended task {uuid} (ran for {diff_mins} mins).")


def show_task(cursor, uuid, showDate=False, showWeekDay=True):
    task = get_task(cursor, uuid)
    if showDate:
        start_time = datetime.fromtimestamp(task[1]).strftime("%a %-d.%-m.: %-H:%M")
    elif showWeekDay:
        start_time = datetime.fromtimestamp(task[1]).strftime("%a: %H:%M")
    else:
        start_time = datetime.fromtimestamp(task[1]).strftime("%H:%M")

    if task[2]:
        end_time = datetime.fromtimestamp(task[2]).strftime(" - %H:%M")
    else:
        end_time = " - ?    "
    return start_time + end_time + f" {task[3]}"


def get_unlogged_task_uuids(cursor):
    cursor.execute(
        """
            SELECT * FROM tasks
            WHERE is_logged IS FALSE
            AND end_time IS NOT NULL
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
        print(show_task(cursor, uuid, showDate=True))


def show_all_tasks(cursor):
    print("All recorded tasks:")
    tasks = get_all_tasks(cursor)
    for task in tasks:
        print(show_task(cursor, task[0], showDate=True))


def unlog_tasks(cursor):
    cursor.execute("SELECT * FROM last_logged")
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
        task = get_task(cursor, uuid)
        print(f"{task[0]}: {task[3]}")
    cursor.execute("DELETE FROM last_logged;")


def log_tasks(cursor):
    unloggedTaskUUIDs = get_unlogged_task_uuids(cursor)
    if not unloggedTaskUUIDs:
        print("No unlogged tasks found.")
        return
    print("Marked the following tasks as logged:")
    cursor.execute("DELETE FROM last_logged;")
    for uuid in unloggedTaskUUIDs:
        cursor.execute(
            """
        UPDATE tasks
        SET is_logged = ?
        WHERE uuid = ?
        """,
            (True, uuid),
        )
        print(show_task(cursor, uuid))
        cursor.execute(
            """
                INSERT INTO last_logged
                VALUES (?)
                """,
            (uuid,),
        )


def show_db(cursor):
    logging.debug("----------------------- Debug output:")
    tasks = get_all_tasks(cursor)
    for row in tasks:
        logging.debug(row)
    logging.debug("----------------------- Last logged:")
    cursor.execute("SELECT * FROM last_logged")
    for row in cursor.fetchall():
        logging.debug(row)


def show_today_tasks(cursor):
    today = datetime.today().date()
    tasks = get_all_tasks(cursor)
    todayTaskUUIDs = [
        x[0] for x in tasks if datetime.fromtimestamp(x[1]).date() == today
    ]
    total_mins = get_task_lengths_in_mins(cursor, todayTaskUUIDs)
    mins = total_mins % 60
    hours = total_mins // 60
    print(today.strftime(f"Tasks on %a, %-d.%-m. ({hours:02}:{mins:02} spent):"))
    for uuid in todayTaskUUIDs:
        print(show_task(cursor, uuid, showWeekDay=False))


def update_statusbar(cursor):
    if not is_task_running(cursor):
        output = ""
    else:
        cursor.execute("""
        SELECT * FROM tasks
        ORDER BY start_time DESC
        LIMIT 1
        """)
        task = cursor.fetchone()
        name = task[3]
        start_time = datetime.fromtimestamp(task[1]).strftime("%-H:%M")
        output = name + " since " + start_time
    with open(STATUSBAR_FILE, "w") as f:
        f.write(output)


def print_this_week(cursor):
    output = ""
    thisWeekUUIDs = get_this_week_uuids(cursor)
    tasks = []
    for uuid in thisWeekUUIDs:
        task = get_task(cursor, uuid)
        tasks.append(task)
    this_week = str(datetime.today().date().isocalendar()[1])
    this_year = str(datetime.today().date().isocalendar()[0])
    total_mins = get_task_lengths_in_mins(cursor, thisWeekUUIDs)
    hours = total_mins // 60
    mins = total_mins % 60
    if len(this_week) == 1:
        this_week: str = "0" + this_week
    output += f"# KW {this_week} / {this_year} ({hours:02}:{mins:02} spent)\n"

    current_weekday = ""
    for task in tasks:
        start = datetime.fromtimestamp(task[1])
        if start.strftime("%a") != current_weekday:
            weekday_heading = start.strftime("\n## %a %-d.%-m.\n\n")
            current_weekday = start.strftime("%a")
            output += weekday_heading
        output += show_task(cursor, task[0], showWeekDay=False)
        if task[4] == 0:
            output += "*"
        output += "\n"

    CURRENT_WEEK_FILE = ARCHIVE_DIR / f"KW_{this_week}.md"
    with open(CURRENT_WEEK_FILE, "w") as f:
        f.write(output)
    print(output)


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
    diff_mins = int(((datetime.now() - start_time).total_seconds() % 3600) // 60)
    start_time = start_time.strftime("%-H:%M")
    print(
        f'Task "{task[3]}" with UUID {task[0]} is running since {start_time} ({diff_mins} mins).'
    )


def assign_task(cursor):
    import os
    import json
    import urllib.request
    import urllib.parse

    EMAIL = os.environ.get("EMAIL")
    HARVEST_TOKEN = os.environ.get("HARVEST_TOKEN")
    HARVEST_ACCOUNT_ID = os.environ.get("HARVEST_ACCOUNT_ID")
    if None in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN):
        print("Environment variable for Harvest upload is missing.")
        print("Aborting upload.")
        return

    url = "https://api.harvestapp.com/v2/users/me/project_assignments"
    headers = {
        "User-Agent": f"MyIntegration ({EMAIL})",
        "Authorization": "Bearer " + str(HARVEST_TOKEN),
        "Harvest-Account-Id": str(HARVEST_ACCOUNT_ID),
    }

    request = urllib.request.Request(url=url, headers=headers)
    with urllib.request.urlopen(request, timeout=5) as response:
        responseCode = response.getcode()
        if responseCode != 200:
            raise Exception("Request to Harvest failed.")

        responseBody = response.read().decode("utf-8")
        jsonResponse = json.loads(responseBody)

    clients = {}
    for project in jsonResponse["project_assignments"]:
        clientId = str(project["client"]["id"])
        projectId = str(project["project"]["id"])
        if not clientId in clients:
            clients[clientId] = project["client"]["name"], {}
        projects = clients[clientId][1]
        if not projectId in projects:
            projects[projectId] = project["project"]["name"], {}
        for task in project["task_assignments"]:
            taskId = str(task["task"]["id"])
            if not taskId in projects[projectId][1]:
                projects[projectId][1][taskId] = task["task"]["name"]
    clientName = subprocess.run(
        ["fzf"],
        input="\n".join([x[0] for x in clients.values()]),
        text=True,
        capture_output=True,
    ).stdout.strip()
    clientId = next(key for key, val in clients.items() if val[0] == clientName)
    projects = clients[clientId][1]
    projectName = subprocess.run(
        ["fzf"],
        input="\n".join([x[0] for x in projects.values()]),
        text=True,
        capture_output=True,
    ).stdout.strip()
    projectId = next(key for key, val in projects.items() if val[0] == projectName)
    tasks = projects[projectId][1]
    taskName = subprocess.run(
        ["fzf"],
        input="\n".join(tasks.values()),
        text=True,
        capture_output=True,
    ).stdout.strip()
    taskId = next(key for key, val in tasks.items() if val == taskName)

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
    SET projectId = ?
    WHERE uuid = ?
    """,
        (projectId, uuid),
    )
    cursor.execute(
        """
    UPDATE tasks
    SET taskId = ?
    WHERE uuid = ?
    """,
        (taskId, uuid),
    )

    print(f'Attributed task "{task[3]}" to {clientName}/{projectName}/{taskName}.')


def push_unlogged_tasks(cursor):
    import os
    import json
    import urllib.request
    import urllib.parse

    unloggedUUIDs = get_unlogged_task_uuids(cursor)
    if not unloggedUUIDs:
        print("No tasks to be uploaded.")
        return
    for uuid in unloggedUUIDs:
        task = get_task(cursor, uuid)
        time_spent = get_task_length_in_mins(cursor, uuid) / 60

        spent_date = datetime.fromtimestamp(task[1]).strftime("%Y-%m-%d")
        hours = f"{time_spent:.2f}"
        notes = task[3]
        defaultUsed = False
        if task[5]:
            task_id = task[6]
        else:
            task_id = TASK_ID
            defaultUsed = True
        if task[6]:
            project_id = task[6]
        else:
            project_id = PROJECT_ID
            defaultUsed = True
        if defaultUsed:
            print(
                f'Task "{task[3]}" with UUID {uuid} has missing task info + is pushed as default task.'
            )

        data = {
            "spent_date": spent_date,
            "hours": hours,
            "notes": notes,
            "project_id": project_id,
            "task_id": task_id,
        }
        data = urllib.parse.urlencode(data).encode("ascii")

        EMAIL = os.environ.get("EMAIL")
        HARVEST_TOKEN = os.environ.get("HARVEST_TOKEN")
        HARVEST_ACCOUNT_ID = os.environ.get("HARVEST_ACCOUNT_ID")
        if None in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN):
            print("Environment variable for Harvest upload is missing.")
            print("Aborting upload.")
            return

        url = "https://api.harvestapp.com/v2/time_entries"
        headers = {
            "User-Agent": f"MyIntegration ({EMAIL})",
            "Authorization": "Bearer " + str(HARVEST_TOKEN),
            "Harvest-Account-Id": str(HARVEST_ACCOUNT_ID),
        }

        request = urllib.request.Request(url=url, headers=headers, data=data)
        with urllib.request.urlopen(request, timeout=5) as response:
            responseCode = response.getcode()
            if responseCode != 201:
                responseBody = response.read().decode("utf-8")
                jsonResponse = json.loads(responseBody)
                print(json.dumps(jsonResponse, sort_keys=True, indent=2))
                raise Exception(
                    f"Request failed: Couldn't push task {uuid} to Harvest."
                )

    print("Successfully pushed all unlogged tasks to Harvest.")
    log_tasks(cursor)
    print("Successfully logged all pushed tasks.")


def main():
    parser = argparse.ArgumentParser(description="Time logging tool")
    parser.add_argument(
        "-d",
        "--debug",
        help="Output debugging info",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.WARNING,
    )

    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start", help="Start a task")
    next_parser = subparsers.add_parser(
        "next", help="Start a task, stop the previous one."
    )
    start_parser.add_argument("task_name", help="Name of the task")
    next_parser.add_argument("task_name", help="Name of the task")
    rename_parser = subparsers.add_parser("rename", help="Rename last task")
    rename_parser.add_argument("task_name", help="New name of the task")
    show_parser = subparsers.add_parser("show", help="Show past tasks")
    show_parser.add_argument(
        "filter",
        help="Which tasks to show",
        choices=["all", "today", "unlogged"],
    )
    subparsers.add_parser("log", help="Mark all tasks as logged")
    subparsers.add_parser(
        "unlog", help="Undo the last operation that marked tasks logged."
    )
    subparsers.add_parser("status", help="Show info about currently running task")
    subparsers.add_parser("stop", help="Stop current task")
    subparsers.add_parser("assign", help="Assign last task to Harvest task")
    subparsers.add_parser("abort", help="Abort current task")
    subparsers.add_parser("extend", help="Set the last completed task to running")
    subparsers.add_parser("print", help="Print current week in human readable format")
    subparsers.add_parser("push", help="Upload unlogged tasks to Harvest")

    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)

    with sqlite3.connect(TIMETRACK_DB, isolation_level=None) as connection:
        cursor = setup(connection.cursor())
        match args.command:
            case "start":
                start_task(cursor, args.task_name)
            case "next":
                next_task(cursor, args.task_name)
            case "extend":
                extend_task(cursor)
            case "stop":
                stop_task(cursor)
            case "abort":
                abort_task(cursor)
            case "rename":
                rename_task(cursor, args.task_name)
            case "status":
                show_status(cursor)
            case "unlog":
                unlog_tasks(cursor)
            case "log":
                log_tasks(cursor)
            case "push":
                push_unlogged_tasks(cursor)
            case "show":
                match args.filter:
                    case "today":
                        show_today_tasks(cursor)
                    case "unlogged":
                        show_unlogged_tasks(cursor)
                    case "all":
                        show_all_tasks(cursor)
            case "print":
                print_this_week(cursor)
            case "assign":
                assign_task(cursor)
            case _:
                print_this_week(cursor)

        show_db(cursor)
        update_statusbar(cursor)


if __name__ == "__main__":
    main()
