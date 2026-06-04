# Completed features

**Last updated:** 2026-06-05

## Completed Features

### Fan pages (production)

- [x] Home Dashboard — playoff command center, quick/live modes, elimination offseason blocks
- [x] Live Game Center — Layer 1/2/3 architecture + safe mode path
- [x] Live Game Center — always-visible trust strip (status, score, clock, source, last updated)
- [x] Playoff Bracket — full bracket with API sync + demo fallback
- [x] Matchup Lineups — position matchups, curated playoff rotations
- [x] Matchup Intelligence — injury + narrative matchup hub
- [x] Player Playoff Tracker — player story hub, charts, logs
- [x] Legacy Tracker — career playoff legacy framing
- [x] Team History & Leaders — franchise legends board
- [x] Previous Rounds — series history cards per round

### Playoff engine & data

- [x] Factual accuracy audit (2026-06-05) — Knicks 4-0 Cavaliers CF, standout/MVP roster guards, `scripts/audit_factual_accuracy.py`
- [x] Unified `get_merged_playoff_state` with cached builders per round
- [x] Team playoff status vs static profiles (`get_effective_team_profile`)
- [x] Sidebar API auto-sync and demo fallback toggles
- [x] Playoff autorefresh on key pages (~60s)
- [x] Curated playoff starters/subs overrides + outdated player filter
- [x] Offseason outlook copy per eliminated team (`OFFSEASON_OUTLOOK_BY_TEAM`)

### Dev Lab & diagnostics

- [x] Dev Lab page — playoff state, API probes, cache stats, Live GC trace, sandbox
- [x] Headless test API (`get_playoff_state_snapshot`, `resolve_live_game_state`, `build_lineup_matchups`)
- [x] `scripts/qa_bracket_logic.py`, `scripts/test_live_gc_layer1.py`

### Suite integration

- [x] `nba_activity.py` — activity events for Command Center
- [x] `nba_persistent_state.py` — session/disk/cloud persistence
- [x] `suite_resume_launch` — deep link resume
- [x] Cloud persistence checkpoint tags on `dev` (`nba-cloud-persistence-v1`)

### Documentation (2026-06-03)

- [x] `docs/` product documentation system (vision, roadmap, pages, engines)
- [x] `product_docs.py` loader for Dev Lab
- [x] Dev Lab **Product docs** tab (priorities, planned, completed, known issues, full doc viewer)
- [x] `cursor-prompts/` mirrors + `.cursor/rules/nba-app-roadmap-docs.mdc`
- [x] [WORKFLOW.md](./WORKFLOW.md) — mandatory before/after major work
- [x] [SYSTEMS_STATUS.md](./SYSTEMS_STATUS.md) — system completion % for Dev Lab
- [x] Expanded [LIVE_GAME_CENTER.md](./LIVE_GAME_CENTER.md) and [PLAYOFF_ENGINE.md](./PLAYOFF_ENGINE.md) as source of truth
- [x] Dev Lab Product docs — priority, last updated, milestone, progress bars
