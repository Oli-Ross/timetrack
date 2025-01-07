# Time tracking tool

A simple tool to track working hours by task via CLI.

## Setup 

Chmod + link the script:

```bash
chmod +x ./timetrack.py
sudo ln -s "$(pwd)/timetrack.py" /usr/local/bin/task
```

## CLI interface

- `task status`: Show the currently running task: start time, duration, name
- `task start NAME`: Start a new task with the name `NAME`, abort with error if one is running
- `task rename NAME`: Rename last task to `NAME`
- `task next NAME`: Start a new task with the name `NAME`, end any running tasks
- `task extend`: Set the last stopped task to running
- `task stop`: End the current task
- `task abort`: Discard the current task
- `task log`: Mark all tasks logged up to including the last task that was ended and show all tasks who's status changed
- `task unlog`: Undo the last call to `task log`
- `task show {all, today, unlogged}`: Only show tasks that are from this day/unlogged
- `task print`: Pretty print the current week into `${ARCHIVE_DIR}/KW_${XX}.md` + stdout, where `XX` is the current calendar week.
- `task push`: Upload unlogged files to Harvest

On each `task` invocation: 
- Print the current task + time running to a file for the OS statusbar

Using `-d` will dump the entire database for debugging purposes.

## Config

The following config parameters can be edited in the source directly:
```python
TIMETRACK_DB = "timetrack.db"
STATUSBAR_FILE = "/tmp/task"
ARCHIVE_DIR = Path("/tmp")
```

`TIMETRACK_DB` is the storage location of the SQLite database (make sure to use an absolute path). 
`STATUSBAR_FILE` is the file that gets an ultra-short stat on the current running task on each invocation. 
`ARCHIVE_DIR` is where `task print` stores the weekly human-readable reports in Markdown format.

## Harvest integration

In order to successfully push to Harvest, you need to set 3 environment variables:
```bash
export EMAIL=your@email.com
export HARVEST_ACCOUNT_ID=1234
export HARVEST_TOKEN=1234
```
Read the [API doc](https://help.getharvest.com/api-v2/) for more info.

Also, there are 2 more config variables that are currently hardcoded:
```python
PROJECT_ID = 1
TASK_ID = 1
```
These IDs define to which project on Harvest the unlogged tasks are uploaded to.

## Internal architecture

- SQLite database
- Each task has unique UUID
