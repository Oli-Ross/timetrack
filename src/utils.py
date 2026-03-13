import subprocess
import uuid
from datetime import datetime
from typing import Dict, List

from model import Task


def get_task_length_in_mins(task: Task):
    if task.end_time:
        end_time = task.end_time.timestamp()
    else:
        end_time = datetime.now().timestamp()
    return int((float(end_time) - float(task.start_time.timestamp())) / 60)


def get_task_lengths_in_mins(tasks: List[Task]):
    return sum([get_task_length_in_mins(task) for task in tasks])


def fzf(input: Dict, prompt=None) -> str:
    fzfInput = "\n".join([str(key) + ":" + str(val) for key, val in input.items()])
    cmd_line = ["fzf-tmux"]
    if prompt:
        cmd_line.append(f'--prompt="{prompt} "')
    cmd_line.append("-p 80%")
    cmd_line.append("--preview-window=hidden")
    cmd_line.append("--delimiter=:")
    cmd_line.append("--with-nth=2..")
    cmd_line.append('--layout=reverse')
    cmd_line.append('--margin=1')
    cmd_line.append('--height=40%')
    cmd_line.append('--border')
    cmd_line.append('--padding=1')
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
