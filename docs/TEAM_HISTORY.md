# Team history & leaders

**Last updated:** 2026-06-05 · **Build:** `final-refine-2026-06-05`

## Purpose

**Team History & Leaders** (`render_team_history_leaders_page`) shows franchise playoff legends and how current roster players chase historical ranks.

## UX goals

- Hero: franchise playoff legends framing.
- **Mount Rushmore** — four faces fans cite first (titles-weighted from curated board).
- **Milestone countdown cards** — e.g. “Brunson passes Houston with 22 more points.”
- **Current-player movement tracker** — progress bars on active chase lines.
- **Greatest playoff runs** — curated franchise chapters (`FRANCHISE_GREAT_RUNS` + fallback from legends).
- **Active milestones this week** — Brunson/Towns/Wembanyama-style chase lines tied to the current postseason.
- **Greatest playoff games** — `FRANCHISE_GREAT_GAMES` curated catalog + live Finals log when available.
- Sortable leaderboard (points, RPG, APG, steals, blocks, 40-pt games, Finals appearances, etc.).
- Visual history cards (`hist-grid`, `_history_card_html`) for top legends.
- Highlight current players on the board (`_is_current_history_player`).

## Data

- `franchise_history_data(team_name)` — legends list + context string.
- Curated / computed career playoff totals per franchise.

## vs Legacy Tracker

| Surface | Focus |
|---------|--------|
| **Team History** | Franchise catalog + sortable all-time board |
| **Legacy Tracker** | Narrative chase for active stars / career arc + slider toy |

## Requirements

- Board must render for all 16 playoff teams in `TEAM_PROFILES`.
- Sort control state keyed per team (`history_sort_{team}`).

## Planned improvements

- Filter "current roster only" toggle.
- Export leaderboard CSV for research (dev-only link in Dev Lab).
