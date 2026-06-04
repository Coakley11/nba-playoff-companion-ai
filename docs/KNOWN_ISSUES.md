# Known issues

**Last updated:** 2026-06-03

## Known Issues

| Issue | Area | Notes |
|-------|------|-------|
| Monolithic `streamlit_app.py` | Maintainability | ~14k lines; page split planned—update `docs/PAGES.md` when splitting |
| Live GC weight on Cloud | Performance | Full page can timeout; safe mode exists; monitor Layer 3 |
| API empty → demo fallback | Bracket | By design when toggle on; document for fans in UI |
| Stale API roster players | Lineups | Mitigated by curated overrides; verify when trades occur |
| `DEV_MODE = True` in repo | Dev Lab | Hide for fan production (`DEV_MODE = False`) before wide release |
| Reset button deploy | Persistence | Confirm visible reset on Streamlit `dev` after suite module sync |
| Doc/code drift risk | Process | Mitigated by WORKFLOW.md + Cursor rule — still requires discipline on every PR |
| NBA cloud persistence testing | Suite | Paused for heavy perf testing—verify before Finals traffic |

## Technical debt

- Duplicate page label aliases in `PAGE_LABEL_ALIASES` (legacy emoji variants).
- Home live bundle 8s timeout may silently drop live mode—UX copy exists but could be clearer.
- Some offseason teams use generic outlook when not in `OFFSEASON_OUTLOOK_BY_TEAM`.

## Operational notes

- Streamlit Cloud branch should be **`dev`** for daily work.
- Reboot app after `[suite_activity]` secrets changes.
- Run `python scripts/qa_bracket_logic.py` after bracket logic edits.
