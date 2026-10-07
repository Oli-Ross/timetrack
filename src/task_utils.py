from datetime import datetime

from calendar_utils import get_time_from_user
from errors import UserInfoError
from model import Task
from utils import get_short_uuid


def is_task_running():
    return Task.select().where(Task.end_time.is_null(True)).exists()


def get_last_task() -> Task:
    return Task.select().order_by(Task.start_time.desc()).limit(1)[0]


def stop_task(shorten_stop: bool = False):
    assert is_task_running(), "No task currently running!"

    task = get_last_task()
    end_time = datetime.now()
    if shorten_stop:
        hour, minute = get_time_from_user()
        end_time = end_time.replace(hour=hour, minute=minute)

    task.end_time = end_time
    task.save()

    diff_mins = int(((end_time - task.start_time).total_seconds()) / 60)
    print(f'Ended "{task.name}" (ran for {diff_mins} mins).')


def start_task(
    taskId=None, projectId=None, stopPrevious=False, taskName=None, backfill=False
):
    name = taskName or input("Name? ")
    if is_task_running():
        if stopPrevious:
            stop_task()
        else:
            raise UserInfoError("There's currently a task running!")

    if backfill:
        last = get_last_task()
        start_time = last.end_time
    else:
        start_time = datetime.now()
    Task.create(
        uuid=get_short_uuid(),
        start_time=start_time,
        end_time=None,
        name=name,
        is_logged=False,
        taskId=taskId,
        projectId=projectId,
    )
    print(
        f'Started "{name}"'
        + (f" from {start_time.strftime('%H:%M')}" if backfill else "")
        + "."
    )
