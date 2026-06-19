"""One-shot patch: shell-first startup, fast playoff state, activity hooks."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "streamlit_app.py"
text = APP.read_text(encoding="utf-8")
original = text


def replace_once(old: str, new: str, label: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"MISSING block: {label}")
    text = text.replace(old, new, 1)


# --- Static playoff state for fast load ---
STATIC_BLOCK = '''

def _build_static_playoff_state_fast():
    """Demo bracket from static templates — no NBA API calls (Fast Load / Lite Mode)."""
    first = {}
    for key, meta in FIRST_ROUND_SERIES.items():
        first[key] = {
            "conf": meta.get("conf"),
            "round": "First Round",
            "a": meta.get("a"),
            "b": meta.get("b"),
            "a_wins": meta.get("a_wins", 0),
            "b_wins": meta.get("b_wins", 0),
            "winner": meta.get("winner"),
            "games": list(meta.get("games") or []),
        }
    stt = {
        "first": first,
        "second": {},
        "cf": {},
        "finals": {},
        "east_fr": [dict(s) for s in first.values() if s.get("conf") == "East"],
        "west_fr": [dict(s) for s in first.values() if s.get("conf") == "West"],
        "east_sr": [],
        "west_sr": [],
        "east_cf": None,
        "west_cf": None,
        "use_demo_backup": True,
        "api_refresh": False,
    }
    stt["team_status"] = _build_team_status_map(stt)
    return stt


'''

if "_build_static_playoff_state_fast" not in text:
    replace_once(
        "@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC, show_spinner=False)\ndef get_playoff_state_cached",
        STATIC_BLOCK
        + "@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC, show_spinner=False)\ndef get_playoff_state_cached",
        "insert static playoff builder",
    )

replace_once(
    'def get_playoff_state_cached(use_demo_backup: bool = True, api_refresh: bool = True):\n'
    '    """Single cached playoff engine: every round, team status, and series scores in one snapshot."""\n'
    "    first = build_first_round_series_cached(use_demo_backup, api_refresh)",
    'def get_playoff_state_cached(use_demo_backup: bool = True, api_refresh: bool = True):\n'
    '    """Single cached playoff engine: every round, team status, and series scores in one snapshot."""\n'
    "    try:\n"
    "        if _qa_skip_expensive_apis():\n"
    "            return _build_static_playoff_state_fast()\n"
    "    except Exception:\n"
    "        pass\n"
    "    first = build_first_round_series_cached(use_demo_backup, api_refresh)",
    "get_playoff_state_cached fast guard",
)

replace_once(
    "    stt = get_playoff_state_cached(True, False)\n"
    "    st.session_state[VALIDATION_PLAYOFF_STATE_KEY] = stt",
    "    stt = _build_static_playoff_state_fast()\n"
    "    st.session_state[VALIDATION_PLAYOFF_STATE_KEY] = stt",
    "warm validation static",
)

replace_once(
    "    return get_playoff_state_cached(True, False)\n"
    "\n"
    "\n"
    "def _validation_gates_status():",
    "    return _build_static_playoff_state_fast()\n"
    "\n"
    "\n"
    "def _validation_gates_status():",
    "validation playoff fallback",
)

# --- main() shell-first bootstrap ---
OLD_BOOT = """    nba_restored = False
    try:
        from nba_persistent_state import prepare_nba_workspace

        nba_restored = prepare_nba_workspace(st)
    except Exception as exc:
        st.session_state["_nba_restore_error"] = str(exc)[:240]

    _sync_validation_mode_globals()"""

NEW_BOOT = """    from nba_startup import (
        mark_deferred_workspace_sync,
        mark_startup_phase,
        pop_deferred_workspace_sync,
        render_startup_diagnostics,
        should_defer_heavy_startup,
    )

    mark_startup_phase(st, "init", boot_t0)
    restore_t0 = pytime.perf_counter()
    nba_restored = False
    try:
        from nba_persistent_state import prepare_nba_workspace, restore_nba_disk_shell

        restore_nba_disk_shell(st)
        _sync_validation_mode_globals()
        if should_defer_heavy_startup(st):
            mark_deferred_workspace_sync(st)
        else:
            nba_restored = prepare_nba_workspace(st)
    except Exception as exc:
        st.session_state["_nba_restore_error"] = str(exc)[:240]
    try:
        from nba_startup import record_startup_section

        record_startup_section(st, "restore", (pytime.perf_counter() - restore_t0) * 1000.0)
    except Exception:
        pass"""

replace_once(OLD_BOOT, NEW_BOOT, "main bootstrap reorder part 1")

# Header timing after header render
replace_once(
    "            except Exception:\n"
    "                _pp_header.render_nba_suite_header(st)\n"
    "    except Exception:\n"
    "        pass\n"
    "\n"
    "    if _is_lgc_route_early():",
    "            except Exception:\n"
    "                _pp_header.render_nba_suite_header(st)\n"
    "    except Exception:\n"
    "        pass\n"
    "    mark_startup_phase(st, \"header\", boot_t0)\n"
    "\n"
    "    if _is_lgc_route_early():",
    "header timing mark",
)

# Sidebar timing after page radio
replace_once(
    "    page = pages[page_label]\n"
    "    _set_lgc_route_skip_bracket_api(page == \"Live Game Center\")",
    "    page = pages[page_label]\n"
    "    mark_startup_phase(st, \"sidebar\", boot_t0)\n"
    "    _set_lgc_route_skip_bracket_api(page == \"Live Game Center\")",
    "sidebar timing mark",
)

# Legacy tracker player activity
OLD_LEGACY = """    player = st.selectbox(\"Choose player\", player_pool, key=\"legacy_tracker_player\")"""
NEW_LEGACY = """    player = st.selectbox(\"Choose player\", player_pool, key=\"legacy_tracker_player\")
    _lt_sig = (team_name, player)
    if st.session_state.get(\"_nba_legacy_tracker_sig\") != _lt_sig:
        st.session_state[\"_nba_legacy_tracker_sig\"] = _lt_sig
        try:
            from nba_activity import log_legacy_tracker_player

            log_legacy_tracker_player(team_name, player)
        except Exception:
            pass"""

if "_nba_legacy_tracker_sig" not in text:
    replace_once(OLD_LEGACY, NEW_LEGACY, "legacy tracker activity")

# Deferred sync + diagnostics at end of main
OLD_END = """    if not pp.skip_background_persistence(st):
        try:
            sig = (favorite_team, page_label or page)
            if st.session_state.get("_suite_activity_sig") != sig:
                st.session_state["_suite_activity_sig"] = sig
                from nba_activity import log_from_page_context

                log_from_page_context(favorite_team, page, page_label)
        except Exception:
            pass

        try:
            from nba_persistent_state import autosave_nba_state
            from suite_user_persistence import clear_workspace_autosave_block

            autosave_nba_state(st)
            clear_workspace_autosave_block(st, "nba")
        except Exception:
            pass"""

NEW_END = """    if pop_deferred_workspace_sync(st):
        defer_t0 = pytime.perf_counter()
        try:
            from nba_persistent_state import prepare_nba_workspace

            prepare_nba_workspace(st)
        except Exception:
            pass
        try:
            from nba_startup import record_startup_section

            record_startup_section(st, "restore", (pytime.perf_counter() - defer_t0) * 1000.0)
        except Exception:
            pass

    if not pp.skip_background_persistence(st):
        try:
            sig = (favorite_team, page_label or page)
            if st.session_state.get("_suite_activity_sig") != sig:
                st.session_state["_suite_activity_sig"] = sig
                from nba_activity import log_from_page_context

                log_from_page_context(favorite_team, page, page_label)
        except Exception:
            pass

        try:
            from nba_persistent_state import autosave_nba_state
            from suite_user_persistence import clear_workspace_autosave_block

            autosave_nba_state(st)
            clear_workspace_autosave_block(st, "nba")
        except Exception:
            pass

    mark_startup_phase(st, \"complete\", boot_t0)
    render_startup_diagnostics(st, boot_t0)"""

replace_once(OLD_END, NEW_END, "main end deferred sync")

if text == original:
    print("No changes applied (already patched?)")
else:
    APP.write_text(text, encoding="utf-8")
    print("Patched streamlit_app.py successfully")
