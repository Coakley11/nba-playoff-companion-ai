# Live Game Center

**Last updated:** 2026-06-03

## Purpose

**Live Game Center** is the in-game command post: score, clock, period, win probability, lineups, box score, play-by-play, and charts—when layers 2–3 are enabled.

## Layer model

| Layer | Behavior | Default |
|-------|----------|---------|
| **Layer 1** | CDN scoreboard + profile context; fast resolve | Always on |
| **Layer 2** | Analysis tabs (on selection) | Opt-in / auto for live status |
| **Layer 3** | Heavy charts, PBP depth | Opt-in |

**Entry:** `render_live_game_center` → if `_live_gc_safe_mode_active()` → `render_live_game_center_safe`.

## Safe mode

- Controlled by `LIVE_GC_SAFE_MODE` (currently `False` in code; can be toggled for incidents).
- Safe path: Layer 1 only, banner, manual refresh button, emergency manual game entry.
- Use when Cloud latency or API outages break full page.

## Refresh & caching

- Page auto-refresh ~60s via `tick_playoff_state_autorefresh` when route is in `playoff_auto_refresh_pages`.
- Cached feeds: `fetch_cdn_scoreboard_only`, `_scoreboard_stats_today_et`, etc.
- Dev Lab → Live GC tab exposes resolve timing, trace, debug expander.

## Resolution priority (Layer 1)

Documented in `_resolve_live_gc_layer1_fast`:

1. Manual session game (if set)
2. CDN live row for favorite team
3. Profile context fallback (opponent, round, scheduled messaging)

## Requirements

- First paint must not block on Layer 2/3.
- Clear fan messaging when no game (`_live_gc_fan_msg`).
- Home Dashboard links set `page_override` → Live Game Center.
- Win probability via `live_win_probability` / `calculate_win_probability` (testable headless).

## Known constraints

- `NBA_LIVE_AVAILABLE`, `NBA_STATS_AVAILABLE` flags gate some feeds.
- Full GC is heavy; monitor Cloud memory on concurrent users.

## Planned improvements

- Re-enable full GC on Cloud after perf baseline.
- Persist manual live game in suite session for cross-device debug only (dev).
