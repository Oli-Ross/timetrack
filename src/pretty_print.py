from datetime import datetime
from typing import List

from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from calendar_utils import get_week_string
from env import HOURS
from model import DailyTarget, HarvestMeta, HarvestProject, Preset, Task
from utils import get_task_lengths_in_mins


def _hours_to_hhmm_string(hours: float, color: bool = True) -> str:
    whole_hours = int(hours)
    pre_indicator = "[green]" if hours <= 0 else "[yellow]"
    post_indicator = " over" if hours < 0 else ""
    minutes = abs(int((hours - whole_hours) * 60))
    open_hours = str(abs(whole_hours))
    if color:
        return f"{pre_indicator}{open_hours}:{minutes:02}{post_indicator}"
    else:
        return f"{open_hours}:{minutes:02}{post_indicator}"


def show_daily_summary(tasksToday: List[Task], tasksUnlogged: List[Task]):
    hours_harvest = HarvestMeta.select().limit(1)[0].hours
    hours_unlogged = get_task_lengths_in_mins(tasksUnlogged) / 60
    hours_worked = hours_harvest + hours_unlogged
    hours_today = get_task_lengths_in_mins(tasksToday) / 60

    weekly_table = Table(header_style="green", show_edge=False)
    weekly_table.add_column("")
    weekly_table.add_column("Hours")
    weekly_table.add_row(
        f"Target", (f"[red]" if int(HOURS) != 24 else "") + f"{HOURS}.0"
    )
    weekly_table.add_row("Worked", f"")
    if HOURS:
        weekly_table.add_row("[italic]- week", f"{hours_worked:.1f} / {HOURS}")
    else:
        weekly_table.add_row("[italic]- week", f"{hours_worked:.1f}")

    daily_target = DailyTarget.select().limit(1)
    daily_target_set = False
    if daily_target:
        daily_target_set = True
        daily_target_hours = daily_target[0].hours
        daily_target_diff = daily_target_hours - hours_today
        daily_target_indicator = _hours_to_hhmm_string(daily_target_diff)
    if daily_target_set:
        weekly_table.add_row(
            "[italic]- today", f"{hours_today:.1f} / {daily_target_hours}"
        )
    else:
        weekly_table.add_row("[italic]- today", f"{hours_today:.1f}")

    if HOURS:
        open_time_in_hours = float(HOURS) - hours_worked
        doneIndicator = "[yellow]" if open_time_in_hours > 0 else "[green]"
        open_hours = int(open_time_in_hours)
        post_indicator = " overtime" if open_hours < 0 else ""
        minutes_open = abs(int((open_time_in_hours - open_hours) * 60))
        open_hours = str(abs(open_hours))
        weekly_table.add_row("Open", "")
        weekly_table.add_row(
            "[italic]- week",
            doneIndicator + f"{open_hours}:{minutes_open:02}{post_indicator}",
        )
        if daily_target_set:
            weekly_table.add_row(
                "[italic]- today",
                daily_target_indicator,
            )
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
    today.add_column("Project")

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
            HarvestProject.get(task.projectId).name,
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


def list_presets():
    table = Table(header_style="green", show_edge=False)
    table.add_column("Name")
    table.add_column("Task")
    for x in Preset.select():
        table.add_row(f"{x.name}", f"{x.client}/{x.project}/{x.task}")
    panel = Panel(
        table,
        title=f"[magenta]Presets",
        padding=(1, 1),
    )
    Console().print(panel)


def _compact_int(n: int) -> str:
    return f"{n / 1000:5.1f}k".replace(".", ",")


def show_budgets():
    table = Table(header_style="green", show_edge=False, border_style="dim")
    table.add_column("Name", min_width=4, max_width=12)
    table.add_column("Client", min_width=4, max_width=12)
    table.add_column("My Rate", width=8)
    table.add_column("Budget", min_width=27)
    table.add_column("Hours left", min_width=4, max_width=6)
    project_output_none = []
    project_output = []
    for x in HarvestProject.select():
        budget = "-"
        budget_text = " ", " "
        if x.budget:
            fraction = x.budget_spent / x.budget
            budget_color = "green"
            if fraction > 1:
                budget_color = "magenta"
            elif fraction > 0.7:
                budget_color = "yellow"
            budget_text = (
                f"[{budget_color}]  {100 * fraction:5.1f}%",
                f" / {_compact_int(x.budget)} $",
            )
            budget = ProgressBar(
                total=1,
                completed=fraction,
                width=8,
                complete_style=budget_color,
                finished_style=budget_color,
            )
        name = f"{x.name}"
        client = f"{x.client.name}"
        hours_left = (
            f"{x.budget_remaining / x.hourly_rate:6.1f}"
            if x.budget_remaining and x.hourly_rate
            else "-"
        )
        row = (
            f"{name:35.35}",
            client,
            f"{int(x.hourly_rate):>3} $/h",
            budget,
            budget_text,
            hours_left,
        )
        if x.budget:
            project_output.append(row)
        else:
            project_output_none.append(row)
    for row in project_output:
        budget_cell = Table.grid()
        budget_cell.add_column()
        budget_cell.add_column()
        budget_cell.add_column()
        budget_cell.add_row(row[3], row[4][0], row[4][1])
        table.add_row(row[0], row[1], row[2], budget_cell, row[5])
        table.add_section()

    panel = Panel(table, title="[magenta]Budgets", padding=(1, 1), expand=False)
    Console().print(panel)
