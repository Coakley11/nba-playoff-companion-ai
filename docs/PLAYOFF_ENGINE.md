# Playoff engine

**Last updated:** 2026-06-03

## Purpose

Unified **playoff bracket state** drives bracket UI, team status (active vs eliminated), round labels, opponents, and Home/Live GC context. Static `TEAM_PROFILES` seed the universe; the engine merges API results and optional demo fallback.

## Key functions

| Function | Role |
|----------|------|
| `get_playoff_state_cached` | Cached snapshot; TTL `PLAYOFF_STATE_CACHE_TTL_SEC` |
| `get_merged_playoff_state` | Demo + API merge for rendering |
| `get_team_playoff_status` | Bracket-derived status for a team |
| `get_effective_team_profile` | Static profile overridden by engine when series active |
| `get_display_matchup` | Opponent, series record, round for UI ribbons |
| `series_for_team` | Series object for favorite team |
| `build_*_round_series_cached` | First / second / CF / finals builders |

## Data sources

1. **NBA API** — `fetch_completed_games_recent` (playoff completed games).
2. **Demo fallback** — bundled local scores when API empty (sidebar: "Use playoff fallback when API is empty").
3. **Auto-sync** — sidebar toggle refreshes bracket on timer (`PLAYOFF_BRACKET_REFRESH_MS`).

## Team status rules

- **Active** — team still in merged bracket with live series.
- **Eliminated** — out of bracket; Home switches to offseason mode; sidebar label `(offseason outlook)`.
- **Effective profile** — may differ from static `TEAM_PROFILES` when API advances a series.

## UI consumers

- Playoff Bracket page
- Home Dashboard ribbon + hero context
- Live Game Center opponent/round hints
- Dev Lab → Playoff state / Bracket tabs
- Headless: `get_playoff_state_snapshot()` for `scripts/qa_bracket_logic.py`

## Requirements (do not regress)

- Never show a blank bracket when demo fallback is enabled and API is empty.
- Series advancement must match game wins in completed-game feed.
- Eliminated teams must not show "Go live" on Home as primary CTA.

## Planned improvements

- CI gate on `qa_bracket_logic.py` for every `dev` push.
- Config-driven round labels for future seasons (reduce hard-coded 2026 strings).
