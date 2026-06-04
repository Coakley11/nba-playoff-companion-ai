# Development priorities

**Last updated:** 2026-06-04

**Active phase:** [PHASE_STABILITY.md](./PHASE_STABILITY.md) — stability, correctness, polish (not new features).

## Current Priorities

### P1 — Live Game Center reliability (highest)

- [x] Phase charter in [PHASE_STABILITY.md](./PHASE_STABILITY.md)
- [x] **Trust strip** on every Live GC path (score, clock, status, source, last updated)
- [ ] Verify safe mode during real game (manual + Dev Lab checklist)
- [ ] Cloud Layer 1: CDN resolve &lt; 3s typical; no blank board on refresh
- [ ] **Freeze** new Live GC features until Layer 1 sign-off ([LIVE_GAME_CENTER.md](./LIVE_GAME_CENTER.md))

### P2 — Home Dashboard speed

- [ ] Section timing in perf footer (identify slowest blocks)
- [ ] Quick view first paint target &lt; 3s on Streamlit Cloud
- [ ] Confirm 8s live bundle timeout UX is acceptable
- [ ] Cache audit: `get_playoff_state_cached`, `resolve_home_matchup_context_fast`

### P3 — Matchup Lineups accuracy

- [ ] Audit `CURRENT_PLAYOFF_LINEUPS` vs expected Finals rotations
- [ ] Verify `OUTDATED_PLAYOFF_PLAYERS` for traded/injured players
- [ ] Lineup source caption accurate in UI

### P4 — NBA Finals state correctness

- [ ] Run `scripts/qa_bracket_logic.py` — zero failures on `dev`
- [ ] Active vs eliminated: bracket, Home, engine agree (Dev Lab team table)
- [ ] Offseason mode only for eliminated teams

### P5 — UI/UX polish (after P1–P4)

- [ ] Header / color / hierarchy pass on main pages
- [ ] Reduce scroll on Home and Live GC
- [ ] Set `DEV_MODE = False` before wide fan release

### P6 — Documentation discipline (ongoing)

- [x] Docs-first workflow ([WORKFLOW.md](./WORKFLOW.md))
- [ ] Update [SYSTEMS_STATUS.md](./SYSTEMS_STATUS.md) when each P1–P4 item completes
- [ ] Same-commit doc updates for every stability fix

### Done — Documentation foundation

- [x] `docs/` source of truth, Dev Lab Product docs, Cursor rule
- [x] `LIVE_GAME_CENTER.md` and `PLAYOFF_ENGINE.md` authoritative

## Next Milestones

| Milestone | Target | Done when |
|-----------|--------|-----------|
| **Live GC game-night ready** | Next live game | Trust strip + scoreboard verified in browser |
| **Cloud smoke pass** | 2026-06 | All pages, active + eliminated team, `dev` deploy |
| Docs system live | 2026-06 | ✓ Complete |
| Module split | Offseason | Deferred |

## Next Features

**Frozen** until [PHASE_STABILITY.md](./PHASE_STABILITY.md) milestone completes. See [ROADMAP.md](./ROADMAP.md) backlog only.

## Notes

- Branch **`dev`** for daily work.
- Read [APP_VISION.md](./APP_VISION.md) → this file → feature doc before any change.
- Do not expand feature surface area during stability phase.
