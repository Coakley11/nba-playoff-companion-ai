# Validation status (P1–P4 gate)

**Last updated:** 2026-06-05 · **Branch:** `dev` only until gates pass.

Do **not** start UI polish until every **Pass** column below is checked during real usage (browser + Cloud).

Automated helpers: `python scripts/validate_stability_phase.py`, `python scripts/audit_lineups.py`

---

## P1 — Live Game Center (browser, during live Finals game)

| Check | Pass | Notes |
|-------|------|-------|
| Trust strip: Status, Score, Clock, Source, Last updated | ☐ | Full + safe mode |
| 2–3 auto-refresh cycles (~60s) | ☐ | No freeze / hang |
| No fake 0–0 mid-game (Q1+) | ☐ | Code guard + eyeball |
| Last-known score when CDN lags | ☐ | Stale banner visible |
| Emergency score entry overrides feed | ☐ | Disable restores feed |

**Dev Lab:** Product docs → Live GC game-night checklist · session log after visiting Live GC.

---

## P2 — Cloud smoke pass (after `dev` redeploy)

| Check | Pass | Notes |
|-------|------|-------|
| Dev Lab → Product docs loads | ☐ | |
| Stability phase + PHASE_STABILITY.md | ☐ | |
| Active priority = P1 | ☐ | |
| Current milestone visible | ☐ | |
| Completion % bars render | ☐ | |
| Home — Knicks (active) | ☐ | |
| Home — eliminated team (offseason) | ☐ | |
| Bracket — Knicks vs Spurs Finals | ☐ | |
| Live GC — trust strip | ☐ | |
| Lineups — Finals rotations | ☐ | |

---

## P3 — Home performance (Show performance debug ON)

Record **top 3 slowest** from Home → Page status (developer):

| Rank | Section | ms | Pass |
|------|---------|-----|------|
| 1 | | | ☐ |
| 2 | | | ☐ |
| 3 | | | ☐ |

**Expected hotspots (code):** `current_game_watch` (CDN Layer 1), `live_bundle` (≤8s), `matchup_ribbon` / `hero_first_paint` (cached playoff state).

Target: quick view first paint &lt; 3s on Cloud after tuning top section.

---

## P4 — Lineups + Finals state

| Check | Pass | Notes |
|-------|------|-------|
| `audit_lineups.py` exits 0 | ☐ | Knicks/Spurs curated vs profiles |
| `validate_stability_phase.py` exits 0 | ☐ | Docs + static Finals teams |
| Knicks + Spurs active; others offseason | ☐ | Sidebar, Home, ribbon |
| Bracket Finals NYK–SAS | ☐ | |
| Previous Rounds — Finals card | ☐ | Active teams only |
| Legacy Tracker — live vs postmortem | ☐ | Active forecast / elim postmortem |

---

## Blocked until above pass

- UI polish (headers, gradients, cards, reduced scroll)
- New features / Live GC Layer 2–3 expansion
