# Development priorities

**Last updated:** 2026-06-03

## Current Priorities

### P0 — Documentation & product discipline

- [x] Establish `docs/` as source of truth for vision, pages, engines.
- [x] Dev Lab **Product docs** tab reading markdown roadmap files (`product_docs.py`).
- [x] Cursor rule `.cursor/rules/nba-app-roadmap-docs.mdc`.
- [x] `cursor-prompts/` mirrors linked to `docs/`.
- [ ] Read `docs/PAGES.md` + area doc before any Live GC or bracket engine change.

### P1 — Deploy & stability

- [ ] Confirm Streamlit Cloud **`dev`** deploys latest `streamlit_app.py` without import errors.
- [ ] Validate Live Game Center Layer 1 on Cloud (CDN scoreboard, refresh loop).
- [ ] Set `DEV_MODE = False` on production fan deploy when diagnostics no longer needed in sidebar.

### P2 — Suite persistence

- [ ] Verify `nba_persistent_state` + reset controls on Cloud (`dev` branch).
- [ ] Cross-device: resume team/page from Command Center deep link.
- [ ] Run `sync_suite_cloud_modules.py` from Command Center after shared module edits.

## Next Milestones

| Milestone | Target | Done when |
|-----------|--------|-----------|
| Docs system live | 2026-06 | Dev Lab shows priorities from `docs/*.md` |
| Cloud smoke pass | 2026-06 | All PAGES routes render for Knicks + eliminated team |
| Full Live GC | Before Finals | `LIVE_GC_SAFE_MODE = False` on Cloud |
| Module split spike | Offseason | `pages/` package + unchanged UX |

## Next Features

*(See [ROADMAP.md](./ROADMAP.md) for backlog; pick up after P1.)*

## Notes

- Work on branch **`dev`**; merge to `main` only for intentional production release.
- Heavy logic stays testable via headless functions at bottom of `streamlit_app.py`.
- Do not implement features that contradict `docs/PAGES.md` without updating docs first.
