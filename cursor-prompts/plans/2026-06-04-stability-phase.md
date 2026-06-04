# Plan: Stability phase (2026-06-04)

**Authoritative:** [docs/PHASE_STABILITY.md](../../docs/PHASE_STABILITY.md)

## Goal

Stable, polished, trustworthy — not new features. Milestone: **Live GC during a real game** + **Cloud smoke pass**.

## Priority order

1. Live Game Center reliability (trust strip, safe mode, Layer 1 freeze)
2. Home Dashboard speed (section ms in perf footer)
3. Matchup Lineups accuracy
4. NBA Finals state correctness
5. UI/UX polish (after 1–4)
6. Documentation discipline

## In progress (this session)

- [x] `PHASE_STABILITY.md` + priorities / systems status / roadmap freeze
- [x] `_render_live_gc_trust_strip` on full + safe paths
- [x] Home Dashboard section timing (`SHOW_PERF_DEBUG`)
- [ ] Game-night manual verification
- [ ] Cloud smoke pass on `dev`

## Do not

- Add Live GC Layer 2/3 features
- Add Home Dashboard sections
- Split `streamlit_app.py` unless required for P1
