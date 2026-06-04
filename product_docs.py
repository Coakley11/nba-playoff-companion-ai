"""
Load product / roadmap markdown from ``docs/`` for Dev Lab and tooling.

The ``docs/`` folder is the source of truth for vision, roadmap, and page requirements.
See ``docs/WORKFLOW.md`` for required read/update rules before and after major work.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

DOCS_DIR = Path(__file__).resolve().parent / "docs"

TRACKED_DOC_FILES: tuple[str, ...] = (
    "APP_VISION.md",
    "PHASE_STABILITY.md",
    "DEVELOPMENT_PRIORITIES.md",
    "ROADMAP.md",
    "WORKFLOW.md",
    "SYSTEMS_STATUS.md",
    "PLAYOFF_ENGINE.md",
    "LIVE_GAME_CENTER.md",
    "PAGES.md",
    "COMPLETED_FEATURES.md",
    "KNOWN_ISSUES.md",
)

DOC_INDEX: tuple[tuple[str, str], ...] = (
    ("WORKFLOW.md", "Workflow (required)"),
    ("APP_VISION.md", "App vision"),
    ("ROADMAP.md", "Roadmap"),
    ("PHASE_STABILITY.md", "Stability phase (active)"),
    ("VALIDATION_STATUS.md", "Validation status (P1–P4)"),
    ("DEVELOPMENT_PRIORITIES.md", "Development priorities"),
    ("SYSTEMS_STATUS.md", "Systems status"),
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


def parse_last_updated(text: str) -> str | None:
    """Parse ``**Last updated:** YYYY-MM-DD`` from doc header."""
    m = re.search(r"\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else None


def docs_freshness() -> dict[str, str | None]:
    """Per-file last updated dates for tracked docs."""
    out: dict[str, str | None] = {}
    for name in TRACKED_DOC_FILES:
        out[name] = parse_last_updated(read_doc(name))
    return out


def latest_doc_update() -> str:
    """Most recent Last updated across tracked docs."""
    dates = [d for d in docs_freshness().values() if d]
    return max(dates) if dates else "—"


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


def extract_active_priority() -> str:
    """First open task or P0/P1 block headline from priorities docs."""
    for fname in ("SYSTEMS_STATUS.md", "DEVELOPMENT_PRIORITIES.md"):
        body = section_by_titles(fname, "Active priority", "Active Priority", "Current Priorities", "Current priorities")
        if not body:
            continue
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("- [ ]"):
                return stripped.replace("- [ ]", "").strip() or stripped
            if stripped.startswith("**P") and "—" in stripped:
                return stripped
        first = next((ln.strip() for ln in body.splitlines() if ln.strip() and not ln.startswith("#")), "")
        if first:
            return first[:200]
    return "—"


def extract_current_milestone() -> str:
    """Current milestone row or SYSTEMS_STATUS current milestone section."""
    direct = section_by_titles("SYSTEMS_STATUS.md", "Current milestone", "Current Milestone")
    if direct:
        line = next((ln.strip() for ln in direct.splitlines() if ln.strip() and not ln.startswith("|")), "")
        if line:
            return line[:240]
    table = section_by_titles("DEVELOPMENT_PRIORITIES.md", "Next Milestones", "Next milestones")
    if not table:
        return "—"
    rows = [ln for ln in table.splitlines() if ln.strip().startswith("|") and "---" not in ln]
    if len(rows) >= 2:
        header = rows[0]
        data = rows[1]
        if "Milestone" in header:
            parts = [c.strip() for c in data.split("|") if c.strip()]
            if parts:
                return parts[0][:240]
    return "—"


def parse_systems_completion() -> list[dict[str, Any]]:
    """
    Parse SYSTEMS_STATUS.md completion table.

    Expects: | System | Completion % | Doc | Notes |
    """
    table = section_by_titles("SYSTEMS_STATUS.md", "System completion", "Systems completion")
    if not table:
        return []
    rows: list[dict[str, Any]] = []
    for line in table.splitlines():
        if not line.strip().startswith("|") or "---" in line or "System" in line and "Completion" in line:
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 2:
            continue
        name = cells[0]
        pct_raw = cells[1].replace("%", "").strip()
        try:
            pct = int(float(pct_raw))
        except ValueError:
            pct = 0
        doc = cells[2] if len(cells) > 2 else ""
        rows.append({"system": name, "pct": min(100, max(0, pct)), "doc": doc})
    return rows


def roadmap_snapshot() -> dict[str, Any]:
    """Structured content for Dev Lab dashboard cards."""
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
        "workflow": section_by_titles("WORKFLOW.md", "Before major work", "Documentation-first workflow"),
        "active_priority": extract_active_priority(),
        "current_milestone": extract_current_milestone(),
        "last_updated": latest_doc_update(),
        "freshness": docs_freshness(),
        "systems": parse_systems_completion(),
    }


def workflow_checklist() -> list[str]:
    """Short checklist for Dev Lab display."""
    return [
        "Before major work: APP_VISION → DEVELOPMENT_PRIORITIES → feature doc",
        "After major work: COMPLETED_FEATURES + KNOWN_ISSUES + feature doc",
        "Major features: update docs in same commit as code",
        "Live GC: LIVE_GAME_CENTER.md · Bracket: PLAYOFF_ENGINE.md",
    ]
