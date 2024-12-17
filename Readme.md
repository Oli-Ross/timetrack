# Time tracking tool

A simple tool to track working hours by task via CLI.

## CLI interface

- `task status`: Show the currently running task: start time, duration, name
- `task start NAME`: Start a new task with the name `NAME`, abort with error if one is running
- `task end`: End the current task
- `task log`: Mark all tasks logged up to including the last task that was ended and show all tasks who's status changed
- `task filter {week, day, unlogged}`: Only show tasks that are from this week/this day/unlogged

On each `task` invocation: 
- Print the current week to `current_week.md` in human readable format
- Print the current task + time running to a file for the OS statusbar

## Internal architecture

- SQLite database
- Each task has unique UUID
