# Time tracking tool

A simple tool to track working hours by task via CLI.
The tracked tasks can be pushed to Harvest (you will be prompted to interactively select which Harvest project/task to assign a
task to). The hours worked in that week will be synced back. 
However, edits on Harvest are not synced back.
This allows you to edit the final remote timesheet without having to maintain a 1:1 relationship with the local db.

## Status

This tool is under active development and may be subject to breaking changes.
Check out the [issues page](https://github.com/Oli-Ross/timetrack/issues) for known issues.

## Setup 

Set up venv, install dependencies + package:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
alias task="$(which python) $(realpath src/app.py)"
```

Then set up your environment as needed (see [Config section](#config)).

To initialize the SQLite database:
```bash
task setup
```

If you add the alias to your `ZSHRC/BASHRC`, make sure to link to the Python binary of the virtual environment.
[fzf](https://github.com/junegunn/fzf) is needed for interaction, make sure that `fzf` is available in your path.

## Basic usage / CLI interface

See [Doc.md](./Doc.md) for documentation on how to use the CLI.

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
export HOURS="10"
```
`ARCHIVE_DIR` is where `task print` stores the weekly human-readable reports in Markdown format.
`STATUSBAR_FILE` is the file that gets an ultra-short stat on the current running task on each change. 
`TIMETRACK_DB` is the storage location of the SQLite database (make sure to use an absolute path). 
`PROJECT_ID` and `TASK_ID` define to which default project/task on Harvest the unlogged tasks are uploaded to, if they have not been assigned.
`HOURS` defines how many hours per week need to be worked, to compute the remaining time.

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
