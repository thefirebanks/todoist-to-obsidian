---
name: todoist-to-obsidian
description: Use when helping a user install, configure, run, schedule, troubleshoot, or safely edit configuration for todoist-to-obsidian, a local CLI that imports Todoist capture tasks into Markdown notes in an Obsidian vault.
metadata:
  short-description: Operate the todoist-to-obsidian CLI safely
---

# todoist-to-obsidian

Use the `todoist-to-obsidian` CLI as the source of truth. Prefer running commands and inspecting generated config over guessing paths or scheduler state.

## Safety Rules

- Never print, log, commit, or repeat a Todoist API token.
- Do not read or display the private `.env` token file unless the user explicitly asks, and even then redact token values.
- Keep alias targets relative to the configured Obsidian vault.
- Do not write notes outside the configured vault path.
- Use placeholder paths and note names in examples.
- For troubleshooting, run `todoist-to-obsidian run --dry-run` before a live import when possible.

## Install

If the command is missing, install with the user's preferred path:

```sh
pipx install git+https://github.com/thefirebanks/todoist-to-obsidian.git
```

For non-Python users, use the platform installer from the project README. Do not pipe remote scripts into a shell without telling the user what command will run.

## Initial Setup

1. Ask the user to create a Todoist project for capture, commonly `obs`.
2. Run the interactive setup:

```sh
todoist-to-obsidian init
```

3. Let the user paste their Todoist API token into the terminal prompt. Do not ask them to paste it into chat.
4. Ask for the Obsidian vault path, default note path, and any aliases.
5. Confirm setup with a dry run:

```sh
todoist-to-obsidian run --dry-run
```

## Capture Syntax

With a Todoist project named `obs`, Raycast Todoist Quick Add examples look like:

```text
remember to send launch notes #obs
ideas: try a shorter onboarding flow #obs
project: follow up on vendor contract #obs
```

Alias prefixes such as `ideas:` and `project:` route to configured note paths. Captures without an alias prefix go to the default note.

## Common Commands

Run once:

```sh
todoist-to-obsidian run
```

Show the config path:

```sh
todoist-to-obsidian config path
```

Install an hourly schedule:

```sh
todoist-to-obsidian schedule install --every 1h
```

Install a daily schedule:

```sh
todoist-to-obsidian schedule install --daily-at 21:30
```

Check scheduler status:

```sh
todoist-to-obsidian schedule status
```

## Config Edits

When editing config for the user:

1. Get the config path with `todoist-to-obsidian config path`.
2. Read `config.toml`; it should not contain the Todoist token.
3. Preserve unrelated user settings.
4. Add aliases under `[aliases]` as relative paths:

```toml
[aliases]
ideas = "Notes/ideas.md"
project = "Projects/project notes.md"
```

5. Validate with `todoist-to-obsidian run --dry-run`.

## Troubleshooting

- If no tasks import, confirm the Todoist project name in config matches the project used in Todoist Quick Add.
- If a label filter is configured, confirm tasks include the matching Todoist label, such as `@capture`.
- If aliases do not route, confirm the task starts with the alias and a colon, such as `ideas:`.
- If scheduling does not run, check `todoist-to-obsidian schedule status` and then run once manually to separate scheduler issues from config issues.
- If a permission error mentions `.env`, the token file is too broadly readable on macOS/Linux; rerun setup or restrict it to user-only permissions.
