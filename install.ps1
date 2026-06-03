$Package = "todoist-to-obsidian"

if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv tool install $Package
} elseif (Get-Command pipx -ErrorAction SilentlyContinue) {
    pipx install $Package
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -m pip install --user $Package
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python -m pip install --user $Package
} else {
    Write-Error "Install Python 3.11+, uv, or pipx, then rerun this installer."
    exit 1
}

Write-Host "Installed $Package"
Write-Host "Run: todoist-to-obsidian init"
