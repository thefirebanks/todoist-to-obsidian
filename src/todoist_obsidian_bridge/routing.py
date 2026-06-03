from __future__ import annotations


def resolve_target_and_content(
    content: str,
    aliases: dict[str, str],
    default_path: str,
) -> tuple[str, str, str | None]:
    stripped = content.strip()
    for alias, target_path in aliases.items():
        prefix = f"{alias}:"
        if stripped.casefold().startswith(prefix.casefold()):
            routed_content = stripped[len(prefix) :].strip()
            return target_path, routed_content or stripped, alias
    return default_path, stripped, None
