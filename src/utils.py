import uuid
from datetime import datetime, timedelta
import subprocess
from typing import List


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
