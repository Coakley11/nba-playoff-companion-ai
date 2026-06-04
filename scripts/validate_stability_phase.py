"""Lightweight stability-phase checks (no Streamlit UI). Run: python scripts/validate_stability_phase.py"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from product_docs import (  # noqa: E402
    DOC_INDEX,
    extract_active_priority,
    extract_current_milestone,
    parse_systems_completion,
    read_doc,
    roadmap_snapshot,
)

FAILURES: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def main() -> int:
    phase = read_doc("PHASE_STABILITY.md")
    check(bool(phase.strip()), "PHASE_STABILITY.md is empty")
    check("ACTIVE" in phase, "PHASE_STABILITY.md missing ACTIVE status")

    names = [n for n, _ in DOC_INDEX]
    check("PHASE_STABILITY.md" in names, "PHASE_STABILITY.md not in Dev Lab DOC_INDEX")

    ap = extract_active_priority()
    check("P1" in ap and "Live Game Center" in ap, f"active priority not P1 Live GC: {ap!r}")

    ms = extract_current_milestone()
    check("Live Game Center" in ms or "Cloud smoke" in ms, f"milestone unexpected: {ms!r}")

    snap = roadmap_snapshot()
    systems = snap.get("systems") or parse_systems_completion()
    check(len(systems) >= 8, f"expected system completion rows, got {len(systems)}")
    check(all(0 <= s["pct"] <= 100 for s in systems), "invalid completion %")

    print("Dev Lab Product Docs smoke")
    print(f"  active_priority: {ap[:80]}...")
    print(f"  current_milestone: {ms[:80]}...")
    print(f"  systems tracked: {len(systems)}")
    print(f"  PHASE_STABILITY.md: {len(phase)} chars")

    app_src = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    check('"status":"Active"' in app_src, "no Active teams in streamlit_app.py")
    active_hits = [
        ln for ln in app_src.splitlines()
        if '"status":"Active"' in ln and ":" in ln.split("{")[0]
    ]
    active_teams = []
    for ln in active_hits:
        name = ln.strip().split(":", 1)[0].strip().strip('"')
        if name:
            active_teams.append(name)
    check(
        set(active_teams) == {"New York Knicks", "San Antonio Spurs"},
        f"expected only Knicks+Spurs active, got {active_teams}",
    )
    check("NYK-SAS" in app_src and "NBA Finals" in app_src, "Finals bracket markers missing")
    print(f"  active teams (static): {', '.join(active_teams)}")

    check("VALIDATION_STATUS.md" in names, "VALIDATION_STATUS.md not in Dev Lab DOC_INDEX")
    val_doc = read_doc("VALIDATION_STATUS.md")
    check(bool(val_doc.strip()), "VALIDATION_STATUS.md empty")
    check("P1 — Live Game Center" in val_doc, "validation checklist missing P1")

    elim_count = app_src.count('"status":"Eliminated"') + app_src.count('"Eliminated"')
    check(elim_count >= 6, f"expected eliminated profile markers, saw ~{elim_count}")

    for marker in (
        "completed playoff postmortem",
        "live forecast",
        "render_previous_rounds_history",
        "_sidebar_team_label",
        "offseason outlook",
    ):
        check(marker in app_src, f"missing Finals view marker: {marker}")

    print("  lineups: run scripts/audit_lineups.py separately")

    if FAILURES:
        print("\nFAILED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("\nOK — docs/Dev Lab metadata ready for Cloud smoke pass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
