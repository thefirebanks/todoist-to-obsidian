from __future__ import annotations

from pathlib import Path


class ObsidianError(RuntimeError):
    pass


def resolve_note_path(vault_path: Path, relative_path: str) -> Path:
    note_path = Path(relative_path)
    if note_path.is_absolute():
        raise ObsidianError(f"Note path must be relative to the vault root: {relative_path}")

    vault_root = vault_path.resolve()
    target_path = (vault_root / note_path).resolve()
    if target_path != vault_root and vault_root not in target_path.parents:
        raise ObsidianError(f"Note path escapes the vault root: {relative_path}")
    return target_path


def append_blocks(vault_path: Path, default_path: str, blocks_by_path: dict[str, list[str]]) -> tuple[list[Path], list[str]]:
    written_paths: list[Path] = []
    warnings: list[str] = []
    default_target_path = resolve_note_path(vault_path, default_path)

    for relative_path, blocks in blocks_by_path.items():
        try:
            target_path = resolve_note_path(vault_path, relative_path)
        except ObsidianError as exc:
            if relative_path == default_path:
                raise
            warnings.append(f"{exc}; falling back to default note.")
            target_path = default_target_path

        if relative_path != default_path and target_path != default_target_path and not target_path.exists():
            warnings.append(f"Alias target does not exist, falling back to default note: {target_path}")
            target_path = default_target_path

        target_path.parent.mkdir(parents=True, exist_ok=True)
        prefix = "\n\n" if target_path.exists() and target_path.stat().st_size > 0 else ""
        with target_path.open("a", encoding="utf-8") as f:
            f.write(prefix + "\n\n".join(blocks).rstrip() + "\n")
        written_paths.append(target_path)

    return written_paths, warnings
