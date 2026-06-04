# Validation status (P1–P4 gate)

**Last updated:** 2026-06-05 · **Branch:** `dev` only until gates pass.

Do **not** start UI polish until every **Pass** column below is checked during real usage (browser + Cloud).

Automated helpers:

- `python scripts/audit_factual_accuracy.py` — engine scores, standouts, Finals teams
- `python scripts/cloud_factual_spotcheck.py` — per-page expected UI snapshot (run before Cloud browser pass)
- `python scripts/audit_lineups.py` — Knicks/Spurs curated boards
- `python scripts/validate_stability_phase.py` — docs + static Finals markers

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

## P5 — Factual accuracy (Cloud UI spot-check)

**Automated preflight:** `python scripts/cloud_factual_spotcheck.py` and `python scripts/audit_factual_accuracy.py` (both exit 0).

**Deploy:** Streamlit Cloud on branch **`dev`** after commit `e1e68e8` or later.

| Page | Pass | What to verify |
|------|------|----------------|
| Home Dashboard — Knicks | ☐ | Finals vs Spurs; series 1–0 (or live API); no offseason blocks |
| Home Dashboard — Cavaliers | ☐ | Eliminated / offseason; East CF loss **4–0** (not 4–2); no active-series CTA |
| Playoff Bracket | ☐ | East CF Knicks **4–0** Cavs; Finals NYK–SAS; eliminated teams greyed/out |
| Previous Rounds — Knicks | ☐ | CF vs Cavs **4–0**; **Game standout** labels; no Trae on Knicks/Hawks wins |
| Matchup Lineups — Knicks | ☐ | Brunson/Bridges/Anunoby/Hart/Towns; bench McBride/Robinson/etc.; headshots match names |
| Matchup Lineups — Spurs | ☐ | Castle/Vassell/Johnson/Sochan/Wembanyama; bench Jones/Champagnie/etc. |
| Player Playoff Tracker — Brunson | ☐ | Stats load; game log **newest first**; Knicks legend comps (Frazier/Ewing lane) |
| Player Playoff Tracker — Wembanyama | ☐ | Duncan/Robinson comps; series cards in playoff order |
| Legacy Tracker — Knicks (active) | ☐ | Live forecast sliders; Brunson/Towns named tier copy |
| Legacy Tracker — Lakers (elim) | ☐ | Postmortem only; no Finals projection sliders |
| Team History — Hawks | ☐ | Jalen Johnson current chase; Trae only in **historical** rows if shown |
| Eliminated offseason — Celtics / Lakers / Hawks / Cavs | ☐ | `OFFSEASON_OUTLOOK_BY_TEAM` copy; no stale starters (Trae, Garland) |

**Known API caveat:** `qa_bracket_logic.py` with `api_refresh=True` may still show **CLE–NYK 4–2** if live NBA feed has six games. Demo backup and UI with demo fallback should show **4–0**. Toggle sidebar demo backup if Cloud bracket disagrees.

---

## Blocked until above pass

- UI polish (headers, gradients, cards, reduced scroll)
- New features / Live GC Layer 2–3 expansion
