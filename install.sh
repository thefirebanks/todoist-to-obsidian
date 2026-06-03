#!/usr/bin/env sh
set -eu

PACKAGE="todoist-to-obsidian"

if command -v uv >/dev/null 2>&1; then
  uv tool install "$PACKAGE"
elif command -v pipx >/dev/null 2>&1; then
  pipx install "$PACKAGE"
elif command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --user "$PACKAGE"
else
  echo "Install Python 3.11+, uv, or pipx, then rerun this installer." >&2
  exit 1
fi

echo "Installed $PACKAGE"
echo "Run: todoist-to-obsidian init"
