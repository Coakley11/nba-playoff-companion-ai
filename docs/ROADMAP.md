# Roadmap — NBA Playoff Companion AI

**Last updated:** 2026-06-03 · **Branch:** `dev`

## Long-Term Vision

- **Single source of truth bracket** — NBA API + demo fallback, zero manual score edits during the postseason.
- **Reliable Live Game Center** — Layer 1 always fast; Layer 2/3 opt-in; safe mode only when needed for stability.
- **Cross-device fan session** — resume last team + page from Command Center Continue links.
- **Richer matchup intelligence** — injury + lineup + recent form in one narrative (without page bloat).
- **Offseason mode as a first-class season phase** — every eliminated team gets structured outlook, not generic filler.
- **Test harness** — headless APIs in `streamlit_app.py` (`get_playoff_state_snapshot`, `resolve_live_game_state`, `build_lineup_matchups`) covered by CI scripts.

## Planned Features

- Re-enable full Live Game Center (disable `LIVE_GC_SAFE_MODE` default) after Cloud performance validation.
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

1. **Docs + Dev Lab product tab** — `docs/` as source of truth; in-app roadmap viewer.
2. **Cloud stability** — confirm `dev` deploy loads all pages under 8s first paint.
3. **Persistence verification** — cloud `full_session` + Command Center activity after real usage.
4. **NBA Finals readiness** — bracket engine + Live GC stress test with concurrent users.
