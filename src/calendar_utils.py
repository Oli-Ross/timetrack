from datetime import datetime


def get_week_string(KW: str | None = None) -> str:
    if not KW:
        this_week = str(datetime.today().date().isocalendar()[1])
    else:
        this_week = str(KW)
    if len(this_week) == 1:
        this_week: str = "0" + this_week
    return this_week
