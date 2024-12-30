# Time tracking tool

A simple tool to track working hours by task via CLI.

## Setup 

Link script:

```bash
chmod +x ./timetrack.py
sudo ln -s "$(pwd)/timetrack.py" /usr/local/bin/task
```

## CLI interface

- `task status`: Show the currently running task: start time, duration, name
- `task start NAME`: Start a new task with the name `NAME`, abort with error if one is running
- `task stop`: End the current task
- `task log`: Mark all tasks logged up to including the last task that was ended and show all tasks who's status changed
- `task unlog`: Undo the last call to `task log`
- `task show {all, week, today, unlogged}`: Only show tasks that are from this week/this day/unlogged
- `task print`: Pretty print the current week into `${ARCHIVE_DIR}/KW_${XX}.md` + stdout, where `XX` is the current calendar week.

On each `task` invocation: 
- Print the current task + time running to a file for the OS statusbar

## Config

The following config parameters can be edited in the source directly:
```python
TIMETRACK_DB = "timetrack.db"
STATUSBAR_FILE = "/tmp/task"
ARCHIVE_DIR = Path("/tmp")
```

`TIMETRACK_DB` is the storage location of the SQLite database. 
`STATUSBAR_FILE` is the file that gets an ultra-short stat on the current running task on each invocation. 
`ARCHIVE_DIR` is where `task print` stores the weekly human-readable reports in Markdown format.


## Internal architecture

- SQLite database
- Each task has unique UUID

## TODO 

Integrate with [Harvest API](https://help.getharvest.com/api-v2/introduction/overview/general/)
