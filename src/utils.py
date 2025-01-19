import uuid
from datetime import datetime, timedelta, date
import subprocess
from typing import List, Dict
from model import Task


def get_task_length_in_mins(task: Task):
    if task.end_time:
        end_time = task.end_time.timestamp()
    else:
        end_time = datetime.now().timestamp()
    return int((float(end_time) - float(task.start_time.timestamp())) / 60)


def get_task_lengths_in_mins(tasks: List[Task]):
    return sum([get_task_length_in_mins(task) for task in tasks])


def daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(days=n)


def get_iso_week_dates(iso_year, iso_week):
    start_date = datetime.strptime(f"{iso_year}-W{iso_week}-1", "%G-W%V-%u").date()
    end_date = start_date + timedelta(days=6)  # End of the week
    return start_date, end_date


def fzf(input: Dict, prompt=None) -> str:
    fzfInput = "\n".join([str(key) + ":" + str(val) for key, val in input.items()])
    cmd_line = ["fzf"]
    if prompt:
        cmd_line.append(f'--prompt="{prompt} "')
    cmd_line.append("--delimiter=:")
    cmd_line.append("--with-nth=2..")
    val = subprocess.run(
        cmd_line,
        input=fzfInput,
        text=True,
        capture_output=True,
    ).stdout.strip()
    if not val:
        raise KeyboardInterrupt("Aborted or `fzf` failed.")
    return val.split(":")[0]


def get_short_uuid():
    return str(uuid.uuid4())[:8]
