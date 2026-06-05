# Legacy Tracker

**Last updated:** 2026-06-05 · **Build:** `premium-fan-2026-06-05`

## Purpose

**Legacy Tracker** frames playoff career achievement with **named franchise comparisons** (Patrick Ewing, Walt Frazier, Tim Duncan, Tony Parker, etc.) and realistic tiers (top 5, top 10, Finals-stage bar).

**Renderer:** `render_legacy_tracker_page(team_name)`

## UX goals

- **Active teams:** locked actuals + forward simulator; `specific_legacy_comparison()` for ladder copy.
- **Eliminated teams:** postmortem only — game log **newest first**, round splits, `specific_legacy_comparison` in section 7.
- No generic “franchise changing” / “one of the greats” language in the comparison engine.

## Premium fan experience (2026-06-05)

- **Earned badge chips** — Franchise Legend, Championship Hero, Finals MVP Track, Top 5 Franchise Player, Greatest Modern Run (fan model; updates with sliders).
- **Impact panel** — title probability impact (% of remaining ceiling), Finals MVP impact bump, all-time franchise rank meter.
- **Franchise GOAT ladder** — top six curated legends with current player highlighted.
- **Playoff run ranking** — contextual copy vs franchise great runs (`FRANCHISE_GREAT_RUNS`).
- Legacy score / ceiling / bracket **meters** + “If playoffs ended today” badge.
- Franchise touchstone face cards + what-if scenario cards (next round / CF / title).
- Plotly path chart moved to collapsed expander for normal-mode first paint.

## Data behavior

- Uses playoff logs, franchise history helpers, and team profile context.
- Respects outdated-player filters (`_is_outdated_playoff_player`) for rotation truth.

## Requirements

- Page must load when team is active or eliminated (legacy story continues in offseason).
- Do not contradict Team History leaders board without documenting difference in [TEAM_HISTORY.md](./TEAM_HISTORY.md).
- **Live Game Center frozen** until P1 game-night sign-off — no changes to Layer 1 from this page.

## Planned improvements

- Share milestone cards (image export).
- Link Legacy Tracker rows → Player Playoff Tracker deep link.
- Normal-mode perf: cache playoff log fetches on Legacy + Player Tracker.
