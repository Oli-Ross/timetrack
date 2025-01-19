# Time tracking tool

A simple tool to track working hours by task via CLI.

## Setup 

Set up venv, install dependencies + package:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
alias task="$(which python) $(realpath src/app.py)"
```

Then set up your environment as needed (see [Config section](#config))

To initialize the SQLite database:
```bash
task setup
```

Then run with `task ${SUBCOMMAND}`.
If you add the alias to your `ZSHRC/BASHRC`, make sure to link to the Python binary of the virtual environment.
[fzf](https://github.com/junegunn/fzf) is needed for interaction, make sure that `fzf` is available in your path.

## CLI interface

- `task status`: Show the currently running task: start time, duration, name
- `task start NAME`: Start a new task with the name `NAME`, abort with error if one is running
- `task rename NAME`: Rename last task to `NAME`
- `task next NAME`: Start a new task with the name `NAME`, end any running tasks
- `task extend`: Set the last stopped task to running
- `task resume`: Start a new instance of a past task
- `task assign`: Interactively select a Harvest project + task to assign to the latest task. Requires `fzf`
- `task stop`: End the current task
- `task abort`: Discard the current task
- `task log`: Mark all tasks logged up to including the last task that was ended and show all tasks who's status changed
- `task unlog`: Undo the last call to `task log`
- `task show {all, today, unlogged}`: Only show tasks that are from this day/unlogged
- `task print`: Pretty print the current week into `${ARCHIVE_DIR}/KW_${XX}.md` + stdout, where `XX` is the current calendar week.
- `task push`: Upload unlogged files to Harvest
- `task pull`: Sync remote data (clients, projects, tasks) to local db
- `task split`: Split a portion off the last task and re-assign it

On each `task` invocation that changes the current task: 
- Print the current task + time running to a file for the OS statusbar

Using `-d` will dump the entire database for debugging purposes.

## Config

Configuration is managed via environment variables.
You can put them in a `.env` file in the top-level directory of this repo or set them in your shell.

The following config parameters are optional and have defaults:
```bash
export ARCHIVE_DIR="/tmp/archive"
export STATUSBAR_FILE="/tmp/task"
export TIMETRACK_DB="/tmp/timetrack.db"
export PROJECT_ID="1"
export TASK_ID="1"
```
`ARCHIVE_DIR` is where `task print` stores the weekly human-readable reports in Markdown format.
`STATUSBAR_FILE` is the file that gets an ultra-short stat on the current running task on each change. 
`TIMETRACK_DB` is the storage location of the SQLite database (make sure to use an absolute path). 
`PROJECT_ID` and `TASK_ID` define to which default project/task on Harvest the unlogged tasks are uploaded to, if they have not been assigned.

In order to successfully push to Harvest, these environment variables are required:
```bash
export EMAIL=your@email.com
export HARVEST_ACCOUNT_ID=1234
export HARVEST_TOKEN=1234
```
Read the [API doc](https://help.getharvest.com/api-v2/) for more info on how to get the token and account ID.

## Internal architecture

- SQLite database, interfaced via `peewee` ORM.
- Separate tables keep track of logged tasks (locally), as well as clients, projects and tasks (as defined by Harvest).
- `fzf` via `subprocess` for user interaction
- [Harvest API](https://help.getharvest.com/api-v2/) for upload
