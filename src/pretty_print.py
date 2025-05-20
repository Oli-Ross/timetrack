from rich.console import Console, Group
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text

from typing import List
from datetime import datetime

from calendar_utils import get_week_string
from model import Task, HarvestMeta
from utils import get_task_lengths_in_mins
from env import HOURS


def show_daily_summary(tasksToday: List[Task], tasksUnlogged: List[Task]):
    hours_harvest = HarvestMeta.select().limit(1)[0].hours
    hours_unlogged = get_task_lengths_in_mins(tasksUnlogged) / 60
    hours_worked = hours_harvest + hours_unlogged
    hours_today = get_task_lengths_in_mins(tasksToday) / 60

    weekly_table = Table(header_style="green", show_edge=False)
    weekly_table.add_column("")
    weekly_table.add_column("Hours")
    weekly_table.add_row("Worked", f"")
    weekly_table.add_row("[italic]- week", f"{hours_worked:.1f}")
    weekly_table.add_row("[italic]- today", f"{hours_today:.1f}")
    if HOURS:
        open = max(float(HOURS) - hours_worked, 0)
        doneIndicator = "[yellow]" if open > 0 else "[green]"
        hours_open = int(open)
        minutes_open = int((open - hours_open) * 60)
        weekly_table.add_row("Open", doneIndicator + f"{hours_open}:{minutes_open:02}")
    if hours_unlogged > 0:
        weekly_table = Group(
            weekly_table, Text("\nThere are unpushed tasks.", style="italic")
        )

    this_year = str(datetime.today().date().isocalendar()[0])
    this_week = get_week_string()
    weekly_panel = Panel(
        weekly_table,
        title=f"[magenta]Summary {this_week} / {this_year[2:4]}",
        padding=(1, 1),
    )

    today = Table(header_style="green", show_edge=False)
    today.add_column("Name")
    today.add_column("When")
    today.add_column("Time")

    formatString = "%H:%M"

    for task in tasksToday:
        start_time = task.start_time.strftime(formatString)
        end_time = task.end_time.strftime(formatString) if task.end_time else "?"
        time_elapsed = task.end_time - task.start_time if task.end_time else None
        logIndicator = "" if task.is_logged else "[yellow]"
        today.add_row(
            logIndicator + f"{task.name}",
            f"{start_time} - {end_time}",
            f"{time_elapsed.seconds // 3600}:{(time_elapsed.seconds // 60) % 60:02}"
            if time_elapsed
            else "",
        )
    this_day = datetime.now().strftime("%A")
    if tasksToday:
        today_panel_content = today
    else:
        today_panel_content = Text("No tasks logged yet.", style="italic")
    today_panel = Panel(
        today_panel_content,
        title=f"[magenta]Today's tasks ({this_day})",
        padding=(1, 1),
    )

    columns = Columns([today_panel, weekly_panel])
    Console().print(columns)
