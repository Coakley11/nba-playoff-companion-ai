# Documentation-first workflow (required)

**Last updated:** 2026-06-04

This project uses **`docs/` as long-term memory**. Code follows docs—not the reverse.

---

## Before major work (required)

Read **in this order**:

1. [APP_VISION.md](./APP_VISION.md) — fan experience goals and product boundaries  
2. [DEVELOPMENT_PRIORITIES.md](./DEVELOPMENT_PRIORITIES.md) — what is active now  
3. **The relevant feature document:**

| If you are changing… | Read first |
|---------------------|------------|
| Live Game Center | [LIVE_GAME_CENTER.md](./LIVE_GAME_CENTER.md) |
| Bracket, team status, elimination | [PLAYOFF_ENGINE.md](./PLAYOFF_ENGINE.md) |
| Home Dashboard, offseason | [PAGES.md](./PAGES.md) + [PLAYOFF_ENGINE.md](./PLAYOFF_ENGINE.md) (offseason) |
| Legacy Tracker | [LEGACY_TRACKER.md](./LEGACY_TRACKER.md) |
| Team History & Leaders | [TEAM_HISTORY.md](./TEAM_HISTORY.md) |
| Matchup / lineups / player pages | [PAGES.md](./PAGES.md) |
| Dev Lab / planning UI | [PAGES.md](./PAGES.md) + this file |

**Major work** = new page behavior, engine rule change, live feed architecture, bracket advancement logic, or any fan-visible workflow change.

---

## After major work (required)

Update **all that apply**:

| File | When |
|------|------|
| [COMPLETED_FEATURES.md](./COMPLETED_FEATURES.md) | Feature shipped or behavior finalized |
| [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) | New bug, debt, or resolved issue |
| Relevant feature doc | Behavior, constants, or requirements changed |
| [SYSTEMS_STATUS.md](./SYSTEMS_STATUS.md) | Completion % or system health changed |
| [DEVELOPMENT_PRIORITIES.md](./DEVELOPMENT_PRIORITIES.md) | Check off tasks; change active P0/P1 |

Also:

- Bump **`Last updated:`** on every edited doc (YYYY-MM-DD).  
- Sync `cursor-prompts/nba_app_*.md` mirrors if Cursor planning files are in use.

---

## Feature requests & new features

When implementing a **major new feature**:

- **Update docs first**, or **in the same commit** as code.  
- Never merge code-only changes that contradict `PAGES.md` or area docs.  
- Add the feature to `COMPLETED_FEATURES.md` when done; remove or check off backlog items in `ROADMAP.md` / `DEVELOPMENT_PRIORITIES.md`.

---

## Source-of-truth map

| Topic | Authoritative doc | Code anchors (reference only) |
|-------|-------------------|-------------------------------|
| Safe mode, layers, refresh | [LIVE_GAME_CENTER.md](./LIVE_GAME_CENTER.md) | `LIVE_GC_SAFE_MODE`, `render_live_game_center*` |
| Advancement, elimination, bracket | [PLAYOFF_ENGINE.md](./PLAYOFF_ENGINE.md) | `get_playoff_state_cached`, `_playoff_status_from_state` |
| Offseason UX | [PLAYOFF_ENGINE.md](./PLAYOFF_ENGINE.md) + [PAGES.md](./PAGES.md) | `_is_home_eliminated`, `render_offseason_*` |

If code and doc disagree, **fix code or doc in the same PR**—do not leave drift.

---

## Dev Lab

**Product docs** tab shows live parsed metadata from these files (via `product_docs.py`). After doc edits, verify the tab in Dev Lab.

---

## Anti-patterns (do not)

- Implement bracket or Live GC changes without reading the area doc.  
- Ship features without updating `COMPLETED_FEATURES.md`.  
- Change `LIVE_GC_SAFE_MODE` or series win rules without updating the matching doc.  
- Let `SYSTEMS_STATUS.md` completion % go stale after large deliveries.
