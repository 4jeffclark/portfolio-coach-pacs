"""Review template helper for skill scripts."""

from __future__ import annotations

from pathlib import Path


def write_review_template(path: Path, title: str, items: list[str]) -> Path:
    lines = [f"# {title}", "", "## Review prompts", ""]
    for item in items:
        lines.append(f"- {item}")
    lines.extend(["", "## User responses", "", "_Agent records verbatim Q&A here._", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
