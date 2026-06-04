# Legacy Tracker

**Last updated:** 2026-06-03

## Purpose

**Legacy Tracker** frames playoff career achievement—where active stars sit on franchise and league playoff leaderboards, chase milestones, and "legacy points" narratives.

**Renderer:** `render_legacy_tracker_page(team_name)`

## UX goals

- Fan-forward copy (not spreadsheet-only).
- Clear separation between **active chase** vs **historical franchise greats**.
- Offseason implications section for eliminated-team context on player pages.
- Tie to playoff game logs and curated player pool.

## Data behavior

- Uses playoff logs, franchise history helpers, and team profile context.
- Respects outdated-player filters (`_is_outdated_playoff_player`) for rotation truth.

## Requirements

- Page must load when team is active or eliminated (legacy story continues in offseason).
- Do not contradict Team History leaders board without documenting difference in [TEAM_HISTORY.md](./TEAM_HISTORY.md).

## Planned improvements

- Share milestone cards (image export).
- Link Legacy Tracker rows → Player Playoff Tracker deep link.
