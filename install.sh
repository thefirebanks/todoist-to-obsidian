#!/usr/bin/env sh
set -eu

SOURCE="git+https://github.com/thefirebanks/todoist-to-obsidian.git"

if command -v uv >/dev/null 2>&1; then
  uv tool install "$SOURCE"
elif command -v pipx >/dev/null 2>&1; then
  pipx install "$SOURCE"
elif command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --user "$SOURCE"
else
  echo "Install Python 3.11+, uv, or pipx, then rerun this installer." >&2
  exit 1
fi

echo "Installed todoist-to-obsidian"
echo "Run: todoist-to-obsidian init"
