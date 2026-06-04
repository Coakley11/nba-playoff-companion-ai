# Roadmap — NBA Playoff Companion AI

**Last updated:** 2026-06-04 · **Branch:** `dev`

**Active phase:** [PHASE_STABILITY.md](./PHASE_STABILITY.md) — new features **frozen** until Live GC + cloud smoke pass.

## Long-Term Vision

- **Single source of truth bracket** — NBA API + demo fallback, zero manual score edits during the postseason.
- **Reliable Live Game Center** — Layer 1 always fast; Layer 2/3 opt-in; safe mode only when needed for stability.
- **Cross-device fan session** — resume last team + page from Command Center Continue links.
- **Richer matchup intelligence** — injury + lineup + recent form in one narrative (without page bloat).
- **Offseason mode as a first-class season phase** — every eliminated team gets structured outlook, not generic filler.
- **Test harness** — headless APIs in `streamlit_app.py` (`get_playoff_state_snapshot`, `resolve_live_game_state`, `build_lineup_matchups`) covered by CI scripts.

## Planned Features

*(Deferred during stability phase — see [PHASE_STABILITY.md](./PHASE_STABILITY.md).)*

- Re-enable full Live Game Center (disable `LIVE_GC_SAFE_MODE` default) after Layer 1 game-night sign-off.
- Visible **Reset to default** on deployed `dev` (suite persistence parity with other apps).
- Expand **Matchup Intelligence** with cached opponent tendencies (pace, ORtg proxy from box logs).
- **Previous Rounds** export/share (markdown or image card) for social posts.
- **Playoff Bracket** — conference finals / finals probability strip (lightweight, no betting framing).
- Automated **bracket QA** in CI (`scripts/qa_bracket_logic.py` on every push to `dev`).
- Split `streamlit_app.py` into page modules (maintain docs in `docs/PAGES.md` as contract).

## Feature backlog

- Mobile-first compact Home Dashboard strip.
- Push-style browser notifications for game tip (experimental).
- Multi-team watch list (secondary teams without losing favorite-team framing).
- Coach's challenge / replay era stats in Live GC (low priority).

## Next Milestones

1. **Live GC game-night ready** — trust strip + real-game verification ([PHASE_STABILITY.md](./PHASE_STABILITY.md)).
2. **Cloud smoke pass** — all pages, active + eliminated team on `dev`.
3. **Home Dashboard speed** — section timing targets met.
4. **Finals state correctness** — engine + UI agree for active/eliminated teams.
5. Persistence verification + NBA Finals load test (after 1–4).
