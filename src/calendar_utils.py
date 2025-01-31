from datetime import datetime, date, timedelta


def get_week_string(KW: str | None = None) -> str:
    if not KW:
        this_week = str(datetime.today().date().isocalendar()[1])
    else:
        this_week = str(KW)
    if len(this_week) == 1:
        this_week: str = "0" + this_week
    return this_week


def daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(days=n)


def get_iso_week_dates(iso_year, iso_week):
    start_date = datetime.strptime(f"{iso_year}-W{iso_week}-1", "%G-W%V-%u").date()
    end_date = start_date + timedelta(days=6)  # End of the week
    return start_date, end_date
