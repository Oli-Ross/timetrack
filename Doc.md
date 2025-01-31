# DOC

## General usage

The syntax is generally `task {SUBCOMMAND}`.
You can run `task -h` to get all subcommands or `task {SUBCOMMAND} -h` to get help for a specific subcommand.

## Subcommands

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
- `task show {all, today, unlogged, week}`: Only show tasks that are from this day/unlogged/week
- `task push`: Upload unlogged files to Harvest
- `task pull`: Sync remote data (clients, projects, tasks) to local db
- `task split`: Split a portion off the last task and re-assign it
- `task edit`: Interactively edit any field of a task
- `task add`: Interactively edit a task retroactively
- `task delete`: Interactively delete a task
- `task preset {add, delete, start, show}`: Manage task presets for common tasks
- `task archive`: Save current week's tasks in human-readable form to archive directory

On each `task` invocation that changes the current task: 
- Print the current task + time running to a file for the OS statusbar

## Debug

Using `-d` will dump the entire database for debugging purposes.
