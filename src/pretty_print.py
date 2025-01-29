from rich.console import Console
from rich.table import Table

from typing import List

from model import Preset


def show_presets(presets: List[Preset]):
    console = Console()

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

    console.print(table)
