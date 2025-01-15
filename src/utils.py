import uuid
from datetime import datetime, timedelta
import subprocess
from typing import List
from model import Task


def get_task_length_in_mins(task: Task):
    if task.end_time:
        end_time = task.end_time.timestamp()
    else:
        end_time = datetime.now().timestamp()
    return int((float(end_time) - float(task.start_time.timestamp())) / 60)


def get_task_lengths_in_mins(tasks: List[Task]):
    return sum([get_task_length_in_mins(task) for task in tasks])


def get_iso_week_dates(iso_year, iso_week):
    start_date = datetime.strptime(f"{iso_year}-W{iso_week}-1", "%G-W%V-%u").date()
    end_date = start_date + timedelta(days=6)  # End of the week
    return start_date, end_date


def fzf(input: List[str], prompt=None) -> str:
    if prompt:
        cmd_line = ["fzf", f'--prompt="{prompt} "']
    else:
        cmd_line = ["fzf"]
    val = subprocess.run(
        cmd_line,
        input="\n".join(input),
        text=True,
        capture_output=True,
    ).stdout.strip()
    if not val:
        raise KeyboardInterrupt("Aborted.")
    return val


def get_short_uuid():
    return str(uuid.uuid4())[:8]
