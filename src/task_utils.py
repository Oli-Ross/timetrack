from utils import get_short_uuid
from model import Task
from datetime import datetime


def is_task_running():
    return Task.select().where(Task.end_time.is_null(True)).exists()


def get_last_task() -> Task:
    return Task.select().order_by(Task.start_time.desc()).limit(1)[0]


def stop_task():
    assert is_task_running(), "No task currently running!"

    task = get_last_task()
    task.end_time = datetime.now()
    task.save()

    diff_mins = int(((datetime.now() - task.start_time).total_seconds()) / 60)
    print(f'Ended "{task.name}" (ran for {diff_mins} mins).')


def start_task(taskId=None, projectId=None, stopPrevious=False):
    name = input("Name? ")
    if is_task_running():
        if stopPrevious:
            stop_task()
        else:
            raise RuntimeError("There's currently a task running!")

    Task.create(
        uuid=get_short_uuid(),
        start_time=datetime.now(),
        end_time=None,
        name=name,
        is_logged=False,
        taskId=taskId,
        projectId=projectId,
    )
    print(f'Started "{name}".')
