# bettersync
A little Python command line utility to make `rsync` easier to use.

## Why
`rsync` is great, but I always find myself struggling to remember folder paths, and even when I remember there's an high chance I'll mistype them. Moreover: most of the time I use the same 2-3 routines repeatedly, so it cries for automation. Finally I wanted to learn how `prompt_toolkit` works, so here we are. Hope it helps!

## Features
- Uses `prompt_toolkit` to suggests source and target folders while typing (with fuzzy autocompletion)
- Stores folders paths in a database, updating the suggestions over time
- Stores the history of `rsync` commands so that repeating the last one is few click away
- Can be initialized with a set of source-target paths
- Easily add controls for specific `rsync` parameters with multiple choice prompts (dryrun only for the moment) 
- Wrap around password prompt (tested)
- Toolbar with keyboard shortcuts suggestions (tested, still not functional)

### Test before release
- Show history 

## TODO
- Dry run should directy lead to not-dryrun without repeting procedure
- Radio button breaks PromptSession app. Avoid it.
- Remove `mnt` as root folder
- History mode: query history for full routines
	- Display nicely: check how to do it with `prompt_toolkit`
- Keyboard shortcuts
	- Shortcut for history mode (Ctrl-H)
	- Go back to previous step and modify (Ctrl-Z)
- Reverse mode or merged mode: instead of separate source and target paths suggestions get their union set
	- update while typing or reload everything?
- Tree exploration for new folders
- Change prompt colors