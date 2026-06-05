# Legacy Tracker

**Last updated:** 2026-06-05 · **Build:** `final-refine-2026-06-05`

## Purpose

**Legacy Tracker** frames playoff career achievement with **named franchise comparisons** (Patrick Ewing, Walt Frazier, Tim Duncan, Tony Parker, etc.) and realistic tiers (top 5, top 10, Finals-stage bar).

**Renderer:** `render_legacy_tracker_page(team_name)`

## UX goals

- **Active teams:** locked actuals + forward simulator; `specific_legacy_comparison()` for ladder copy.
- **Eliminated teams:** postmortem only — game log **newest first**, round splits, `specific_legacy_comparison` in section 7.
- No generic “franchise changing” / “one of the greats” language in the comparison engine.

## Final refinement (2026-06-05)

- **Achievement unlocks** — six locked/unlocked chips that react to sliders and bracket state.
- **Career-defining game alert** — highest-impact playoff night from the log.
- **Legacy swing panel** — win Finals / lose Finals / win next game delta cards.
- **Franchise rank movement** — animated today → win-title rank shift; lose-Finals no-movement callout.
- Prior premium pass: badges, GOAT ladder, title/MVP impact, scenario cards.
- Franchise compare faces + Plotly path in collapsed expanders (first paint = meters + unlocks + swing).

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
