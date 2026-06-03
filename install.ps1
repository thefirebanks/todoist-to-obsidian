$Source = "git+https://github.com/thefirebanks/todoist-to-obsidian.git"

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv tool install $Source
} elseif (Get-Command pipx -ErrorAction SilentlyContinue) {
    pipx install $Source
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -m pip install --user $Source
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python -m pip install --user $Source
} else {
    Write-Error "Install Python 3.11+, uv, or pipx, then rerun this installer."
    exit 1
}

Write-Host "Installed todoist-to-obsidian"
Write-Host "Run: todoist-to-obsidian init"
