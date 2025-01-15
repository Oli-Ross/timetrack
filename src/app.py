#!/usr/bin/env python3

import argparse
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from peewee import fn
from model import Task, LogHistory
from db_config import db
from utils import fzf, get_iso_week_dates, get_short_uuid

TIMETRACK_DB = "./timetrack.db"
STATUSBAR_FILE = "/tmp/task"
ARCHIVE_DIR = Path("./timetrack")

PROJECT_ID = 1
TASK_ID = 1

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

EMAIL = os.getenv("EMAIL")
HARVEST_TOKEN = os.getenv("HARVEST_TOKEN")
HARVEST_ACCOUNT_ID = os.getenv("HARVEST_ACCOUNT_ID")


def get_weeks_tasks(KW=None):
    if KW:
        this_week = str(KW).lstrip("0")
    else:
        this_week = str(datetime.today().date().isocalendar()[1])
    this_year = str(datetime.today().date().isocalendar()[0])
    start_date, end_date = get_iso_week_dates(this_year, this_week)
    tasks = Task.select().where(
        (Task.start_time >= start_date) & (Task.start_time <= end_date)
    )
    return tasks


def get_all_tasks() -> List[Task]:
    return Task.select()


def get_task(uuid) -> Task:
    return Task.select().where(Task.uuid == uuid)[0]


def get_task_length_in_mins(task: Task):
    if task.end_time:
        end_time = task.end_time.timestamp()
    else:
        end_time = datetime.now().timestamp()
    return int((float(end_time) - float(task.start_time.timestamp())) / 60)


def get_task_lengths_in_mins(tasks: List[Task]):
    return sum([get_task_length_in_mins(task) for task in tasks])


def add_task(task_data: Dict[str, str | datetime | bool | None]):
    Task.create(**task_data)


def is_task_running():
    return Task.select().where(Task.end_time.is_null(True)).exists()


def next_task(name: str):
    if is_task_running():
        stop_task()

    uuid = get_short_uuid()
    task_data = {
        "uuid": uuid,
        "start_time": datetime.now(),
        "end_time": None,
        "name": name,
        "is_logged": False,
        "taskId": None,
        "projectId": None,
    }
    add_task(task_data)
    print(f"Started task with UUID {uuid}.")


def resume_task():
    assert not is_task_running(), "There's currently a task running!"

    tasks = Task.select()

    uuid_task = fzf(
        [f"{task.uuid}:\t{task.name}" for task in tasks], prompt="Resume task?"
    )
    uuid = uuid_task.split(":")[0]
    task = [task for task in tasks if task.uuid == uuid][0]
    print(f"Resuming task {task.name}")
    start_task(task.name, task.uuid, task.projectId)


def start_task(name: str, taskId=None, projectId=None):
    assert not is_task_running(), "There's currently a task running!"

    uuid = get_short_uuid()
    task_data = {
        "uuid": uuid,
        "start_time": datetime.now(),
        "end_time": None,
        "name": name,
        "is_logged": False,
        "taskId": taskId,
        "projectId": projectId,
    }
    add_task(task_data)
    print(f"Started task with UUID {uuid}.")


def extend_task():
    assert not is_task_running(), "There's currently a task running!"

    task = Task.select().order_by(Task.start_time.desc()).limit(1)[0]
    task.end_time = None
    task.save()
    print(f'Set task "{task.name}" {task.uuid} to running.')


def rename_task(task_name):
    task = Task.select().order_by(Task.start_time.desc()).limit(1)[0]
    old_name = task.name
    task.name = task_name
    task.save()

    print(f'Renamed "{old_name}" to "{task_name}"')


def abort_task():
    assert is_task_running(), "No task currently running!"

    task = Task.select().order_by(Task.start_time.desc()).limit(1)[0]
    name = task.name
    task.delete_instance()

    print(f'Aborted task "{name}".')


def stop_task():
    assert is_task_running(), "No task currently running!"

    task = Task.select().order_by(Task.start_time.desc()).limit(1)[0]
    task.end_time = datetime.now()
    task.save()

    diff_mins = int(((datetime.now() - task.start_time).total_seconds() / 3600) / 60)
    print(f"Ended task {task.uuid} (ran for {diff_mins} mins).")


def show_task(task: Task, showDate=False, showWeekDay=True):
    if showDate:
        formatString = "%a %-d.%-m.: %-H:%M"
    elif showWeekDay:
        formatString = "%a: %H:%M"
    else:
        formatString = "%H:%M"
    start_time = task.start_time.strftime(formatString)

    if task.end_time:
        end_time = task.end_time.strftime(" - %H:%M")
    else:
        end_time = " - ?    "
    return start_time + end_time + f" {task.name}"


def get_unlogged_tasks():
    return Task.select().where(
        (Task.is_logged == False) & (Task.end_time.is_null(False))
    )


def show_unlogged_tasks():
    print("Unlogged tasks:")
    unloggedTasks = get_unlogged_tasks()
    if not unloggedTasks:
        print("No unlogged tasks found.")
        return
    for task in unloggedTasks:
        print(show_task(task, showDate=True))


def show_all_tasks():
    print("All recorded tasks:")
    for task in get_all_tasks():
        print(show_task(task, showDate=True))


def unlog_tasks():
    lastLoggedTasksHistory = LogHistory.select()
    if not lastLoggedTasksHistory:
        print("No history of logging found - only one undo level is supported.")
        return
    print(f"Reset the following tasks' log status:")
    for logEntry in lastLoggedTasksHistory:
        task = get_task(logEntry.uuid)
        task.is_logged = False
        task.save()
        print(f"{task.uuid}: {task.name}")
    LogHistory.delete().execute()


def log_tasks():
    unloggedTasks = Task.select().where(
        (Task.is_logged == False) & (Task.end_time.is_null(False))
    )
    if not unloggedTasks:
        print("No unlogged tasks found.")
        return
    print("Marked the following tasks as logged:")
    LogHistory.delete().execute()
    for task in unloggedTasks:
        task.is_logged = True
        task.save()
        LogHistory.create(uuid=task.uuid)
        print(show_task(task))


def show_db():
    print("----------------------- Debug output:")
    for row in get_all_tasks():
        print(
            "\n".join(
                "|".join(f"{value}" for _, value in record.__data__.items())
                for record in Task.select()
            )
        )

    print("----------------------- Last logged:")
    for row in LogHistory.select():
        print(row)


def show_today_tasks():
    today = datetime.today()
    todayTasks = Task.select().where(
        fn.strftime("%Y-%m-%d", Task.start_time) == today.strftime("%Y-%m-%d")
    )
    total_mins = get_task_lengths_in_mins(todayTasks)
    mins = total_mins % 60
    hours = total_mins // 60
    print(today.strftime(f"Tasks on %a, %-d.%-m. ({hours:02}:{mins:02} spent):"))
    for task in todayTasks:
        print(show_task(task, showWeekDay=False))


def update_statusbar():
    if not is_task_running():
        output = ""
    else:
        task = Task.select().order_by(Task.start_time.desc()).limit(1)[0]
        output = task.name + " since " + task.start_time.strftime("%-H:%M")
    with open(STATUSBAR_FILE, "w") as f:
        f.write(output)


def get_weekly_harvest_hours(KW=None):
    import json
    import urllib.request
    import urllib.parse

    if None in (EMAIL, HARVEST_ACCOUNT_ID, HARVEST_TOKEN):
        print("Environment variable for Harvest upload is missing.")
        print("Aborting upload.")
        return

    if KW:
        today = datetime.fromisocalendar(datetime.now().year, KW, 2)
    else:
        today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    friday = today + timedelta(days=(4 - today.weekday()))
    fromDate = monday.strftime("%Y%m%d")
    toDate = friday.strftime("%Y%m%d")
    url = f"https://api.harvestapp.com/v2/reports/time/team?from={fromDate}&to={toDate}"
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

    if not jsonResponse["results"]:
        return 0.0

    return jsonResponse["results"][0]["total_hours"]


def print_week(KW=None):
    output = ""
    weekTasks = get_weeks_tasks(KW)
    tasks = []
    for task in weekTasks:
        tasks.append(task)
    if not KW:
        this_week = str(datetime.today().date().isocalendar()[1])
    else:
        this_week = str(KW)
    this_year = str(datetime.today().date().isocalendar()[0])
    total_mins = get_task_lengths_in_mins(weekTasks)
    hours = total_mins // 60
    mins = total_mins % 60
    if len(this_week) == 1:
        this_week: str = "0" + this_week
    hours_harvest = get_weekly_harvest_hours(KW)
    output += f"# KW {this_week} / {this_year} ({hours:02}:{mins:02} spent, {hours_harvest} in Harvest)\n"

    current_weekday = ""
    for task in tasks:
        start = task.start_time
        if start.strftime("%a") != current_weekday:
            weekday_heading = start.strftime("\n## %a %-d.%-m.\n\n")
            current_weekday = start.strftime("%a")
            output += weekday_heading
        output += show_task(task, showWeekDay=False)
        if not task.is_logged:
            output += "*"
        output += "\n"

    CURRENT_WEEK_FILE = ARCHIVE_DIR / f"KW_{this_week}.md"
    with open(CURRENT_WEEK_FILE, "w") as f:
        f.write(output)
    print(output)


def show_status():
    if not is_task_running():
        print("No task currently running!")
        return
    task = Task.select().order_by(Task.start_time.desc()).limit(1)[0]
    diff_mins = int(((datetime.now() - task.start_time).total_seconds() % 3600) // 60)
    start_time = task.start_time.strftime("%-H:%M")
    print(
        f'Task "{task.name}" with UUID {task.uuid} is running since {start_time} ({diff_mins} mins).'
    )


def assign_task():
    import json
    import urllib.request
    import urllib.parse

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
    clientName = fzf([x[0] for x in clients.values()])
    clientId = next(key for key, val in clients.items() if val[0] == clientName)
    projects = clients[clientId][1]
    projectName = fzf([x[0] for x in projects.values()])
    projectId = next(key for key, val in projects.items() if val[0] == projectName)
    tasks = projects[projectId][1]
    taskName = fzf(tasks.values())
    taskId = next(key for key, val in tasks.items() if val == taskName)

    task = Task.select().order_by(Task.start_time.desc()).limit(1)[0]
    task.projectId = projectId
    task.taskId = taskId
    task.save()

    print(f'Attributed task "{task.name}" to {clientName}/{projectName}/{taskName}.')


def push_unlogged_tasks():
    import json
    import urllib.request
    import urllib.parse

    unloggedTasks = get_unlogged_tasks()
    if not unloggedTasks:
        print("No tasks to be uploaded.")
        return
    for task in unloggedTasks:
        time_spent = get_task_length_in_mins(task) / 60

        spent_date = task.start_time.strftime("%Y-%m-%d")
        hours = f"{time_spent:.2f}"
        notes = task.name
        defaultUsed = False
        if task.taskId:
            task_id = task.taskId
        else:
            task_id = TASK_ID
            defaultUsed = True
        if task.projectId:
            project_id = task.projectId
        else:
            project_id = PROJECT_ID
            defaultUsed = True
        if defaultUsed:
            print(
                f'Task "{task.name}" with UUID {task.uuid} has missing task info + is pushed as default task.'
            )

        data = {
            "spent_date": spent_date,
            "hours": hours,
            "notes": notes,
            "project_id": project_id,
            "task_id": task_id,
        }
        data = urllib.parse.urlencode(data).encode("ascii")

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

    log_tasks()
    print("Successfully pushed all unlogged tasks.")


def main():
    parser = argparse.ArgumentParser(description="Time logging tool")
    parser.add_argument(
        "-d",
        "--debug",
        help="Output debugging info",
        action="store_const",
        dest="debug",
        const=True,
        default=False,
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
    subparsers.add_parser("resume", help="Start a new instance of a past task")
    print_parser = subparsers.add_parser(
        "print", help="Print current week in human readable format"
    )
    print_parser.add_argument(
        "--kw", type=int, help="Calendar week to print for.", default=None
    )
    subparsers.add_parser("push", help="Upload unlogged tasks to Harvest")

    args = parser.parse_args()

    with db:
        match args.command:
            case "start":
                start_task(args.task_name)
                assign_task()
                update_statusbar()
            case "next":
                next_task(args.task_name)
                assign_task()
                update_statusbar()
            case "resume":
                resume_task()
                update_statusbar()
            case "extend":
                extend_task()
                update_statusbar()
            case "stop":
                stop_task()
                update_statusbar()
            case "abort":
                abort_task()
                update_statusbar()
            case "rename":
                rename_task(args.task_name)
                update_statusbar()
            case "status":
                show_status()
            case "unlog":
                unlog_tasks()
            case "log":
                log_tasks()
            case "push":
                push_unlogged_tasks()
            case "show":
                match args.filter:
                    case "today":
                        show_today_tasks()
                    case "unlogged":
                        show_unlogged_tasks()
                    case "all":
                        show_all_tasks()
            case "print":
                print_week(args.kw)
            case "assign":
                assign_task()
            case _:
                print_week()

        if args.debug:
            show_db()


if __name__ == "__main__":
    main()

# Log locally
# Push + fetch new hours
# Log locally
# -> Only interact with Harvest when executing push
