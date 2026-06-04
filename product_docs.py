"""
Load product / roadmap markdown from ``docs/`` for Dev Lab and tooling.

The ``docs/`` folder is the source of truth for vision, roadmap, and page requirements.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DOCS_DIR = Path(__file__).resolve().parent / "docs"

DOC_INDEX: tuple[tuple[str, str], ...] = (
    ("APP_VISION.md", "App vision"),
    ("ROADMAP.md", "Roadmap"),
    ("DEVELOPMENT_PRIORITIES.md", "Development priorities"),
    ("PAGES.md", "Pages & UX"),
    ("PLAYOFF_ENGINE.md", "Playoff engine"),
    ("LIVE_GAME_CENTER.md", "Live Game Center"),
    ("LEGACY_TRACKER.md", "Legacy Tracker"),
    ("TEAM_HISTORY.md", "Team history & leaders"),
    ("COMPLETED_FEATURES.md", "Completed features"),
    ("KNOWN_ISSUES.md", "Known issues"),
)


def docs_root() -> Path:
    return DOCS_DIR


def list_doc_files() -> list[Path]:
    if not DOCS_DIR.is_dir():
        return []
    return sorted(DOCS_DIR.glob("*.md"), key=lambda p: p.name.lower())


def read_doc(filename: str) -> str:
    path = DOCS_DIR / filename
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def parse_markdown_sections(text: str) -> dict[str, str]:
    """Split markdown on ``## `` headings; keys are normalized slug labels."""
    sections: dict[str, list[str]] = {"_intro": []}
    current = "_intro"
    for line in text.splitlines():
        if line.startswith("## "):
            current = _slug_heading(line[3:].strip())
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


def _slug_heading(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "_", slug)
    return slug or "section"


def section_by_titles(filename: str, *titles: str) -> str:
    """Return first matching section body (case-insensitive title match)."""
    sections = parse_markdown_sections(read_doc(filename))
    want = {_slug_heading(t) for t in titles}
    for key, body in sections.items():
        if key in want:
            return body
    return ""


def roadmap_snapshot() -> dict[str, Any]:
    """Structured bullets for Dev Lab dashboard cards."""
    return {
        "priorities": section_by_titles(
            "DEVELOPMENT_PRIORITIES.md", "Current Priorities", "Current priorities"
        ),
        "milestones": section_by_titles(
            "DEVELOPMENT_PRIORITIES.md", "Next Milestones", "Next milestones"
        ),
        "planned": section_by_titles(
            "ROADMAP.md", "Planned Features", "Next Features", "Feature backlog"
        ),
        "completed": section_by_titles(
            "COMPLETED_FEATURES.md", "Completed Features", "Completed features"
        ),
        "known_issues": section_by_titles(
            "KNOWN_ISSUES.md", "Known Issues", "Known issues"
        ),
        "vision": section_by_titles("APP_VISION.md", "Product vision", "App vision"),
    }
