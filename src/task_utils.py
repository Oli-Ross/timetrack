from utils import get_short_uuid
from model import Task
from datetime import datetime


def is_task_running():
    return Task.select().where(Task.end_time.is_null(True)).exists()


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
    Task.create(**task_data)
    print(f"Started task with UUID {uuid}.")
