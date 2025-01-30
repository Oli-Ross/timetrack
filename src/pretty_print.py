from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel

from typing import List
from datetime import datetime

from calendar_utils import get_week_string
from model import Preset, Task, HarvestMeta
from utils import get_task_lengths_in_mins
from env import HOURS


def show_presets(presets: List[Preset]):
    table = Table(header_style="green", title="[magenta]Presets")
    table.add_column("Name", style="red", min_width=10)
    table.add_column("Harvest Task")
    table.add_column("Harvest Client/Project")

    for preset in presets:
        table.add_row(
            f"{preset.name}",
            f"{preset.task.name}",
            f"{preset.project.client.name}/{preset.project.name}",
        )

    Console().print(table)


def show_summary(
    tasksToday: List[Task], tasksWeek: List[Task], tasksUnlogged: List[Task]
):
    this_year = str(datetime.today().date().isocalendar()[0])
    this_week = get_week_string()
    hours_harvest = HarvestMeta.select().limit(1)[0].hours
    hours_local = get_task_lengths_in_mins(tasksWeek) / 60
    hours_unlogged = get_task_lengths_in_mins(tasksUnlogged) / 60
    hours_worked = hours_harvest + hours_unlogged

    weekly_table = Table(header_style="green", show_edge=False)
    weekly_table.add_column("")
    weekly_table.add_column("Hours")
    weekly_table.add_row("Worked", f"{hours_worked:.1f}")
    if HOURS:
        hours_open = max(float(HOURS) - hours_worked, 0)
        doneIndicator = "[red]" if hours_open > 0 else "[green]"
        weekly_table.add_row("Open", doneIndicator + f"{hours_open:.1f}")
    weekly_table.add_section()
    weekly_table.add_row("Logged", f"{hours_local:.1f}")
    weekly_table.add_row("Unlogged", f"{hours_unlogged:.1f}")
    weekly_table.add_row("In Harvest", f"{hours_harvest:.1f}")
    weekly_panel = Panel(
        weekly_table,
        title=f"[magenta]Summary {this_week} / {this_year[2:4]}",
        padding=(1, 1),
    )

    today = Table(header_style="green", show_edge=False)
    today.add_column("Name")
    today.add_column("Time")

    formatString = "%H:%M"

    for task in tasksToday:
        start_time = task.start_time.strftime(formatString)
        end_time = task.end_time.strftime(formatString) if task.end_time else "?"
        logIndicator = "" if task.is_logged else "[yellow]"
        today.add_row(logIndicator + f"{task.name}", f"{start_time} - {end_time}")
    today_panel = Panel(today, title="[magenta]Today's tasks", padding=(1, 1))

    columns = Columns([today_panel, weekly_panel])
    console = Console().print(columns)
