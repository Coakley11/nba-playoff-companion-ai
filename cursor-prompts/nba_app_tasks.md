# Current tasks (Cursor mirror)

**Last updated:** 2026-06-05

> **Authoritative:** [docs/DEVELOPMENT_PRIORITIES.md](../docs/DEVELOPMENT_PRIORITIES.md) · **Phase:** [docs/PHASE_STABILITY.md](../docs/PHASE_STABILITY.md)

## Current Priorities (stability phase)

### Fan experience audit (2026-06-05)

- [x] P1 Consistency — product shell, unified trust badges, mobile CSS
- [x] P2 Trust — `render_page_trust_strip` on all fan pages
- [x] P3 Fan testing — trim duplicate disclaimers; keep high-value tiles
- [x] P4 Mobile — stack grids on Home, Tracker, Legacy, Lineups, History
- [x] P5 Perf — no new systems; build `quality-pass-2026-06-05`
- [x] Docs — [docs/FAN_EXPERIENCE_AUDIT.md](../docs/FAN_EXPERIENCE_AUDIT.md)

### P1 — Live Game Center

- [x] Trust strip (`_render_live_gc_trust_strip`) on full + safe paths
- [ ] Verify safe mode during real game
- [ ] Cloud Layer 1 sign-off — freeze new Live GC features

### P2 — Home Dashboard

- [x] Section timing in perf footer (`SHOW_PERF_DEBUG`)
- [x] Fan briefing board — 9-tile energy grid (Game 1→2, coaching, pressure)
- [ ] Identify slowest sections; cache audit
- [ ] Quick view &lt; 3s on Cloud

### Final refinement pass (2026-06-05)

- [x] P1 Player Tracker — journey panel, Finals pass %, title rank projection, team pulse/stock
- [x] P2 Legacy — achievement unlocks, rank movement animation, defining game, legacy swing
- [x] P3 Team History — active milestones this week, FRANCHISE_GREAT_GAMES
- [x] P4 Home — broadcast-studio tile copy (TNT/ESPN tone)
- [x] P5 Perf — more expanders (series tabs, compare, history deep-dive, legacy faces)

### Premium fan experience pass (2026-06-05)

- [x] P1 Player Tracker — record race lane, next 3 / easiest / hardest / series milestones
- [x] P2 Legacy — badges, title/Finals MVP impact, GOAT ladder, run ranking
- [x] P3 Home — sportswriter tile copy (Finals-specific)
- [x] P4 Team History — Mount Rushmore, countdown, movement tracker, great runs/games
- [x] P5 Normal-mode speed — Plotly/season_averages deferred behind expanders

### Polish phase (2026-06-05)

- [x] P1 Player Playoff Tracker visual overhaul (chase board, awards, series tabs, game cards)
- [x] P2 Legacy Tracker meters + scenario cards + franchise faces
- [x] P4 Lineups audit (Harrison Barnes PF, no Jeremy Sochan)
- [x] P5 Normal-mode bottleneck table in `docs/PERFORMANCE_AUDIT.md`

### P3–P6

See [docs/PHASE_STABILITY.md](../docs/PHASE_STABILITY.md).

## Next Milestones

1. Live GC game-night ready
2. Cloud smoke pass (`dev`)
3. Home speed + Finals state correctness

## Next Features

**Frozen** until stability milestone — [docs/ROADMAP.md](../docs/ROADMAP.md).

## Notes

- Branch: `dev`
- Plan: `cursor-prompts/plans/2026-06-04-stability-phase.md`
