"""Patch NBA streamlit_app.py for aggressive shell-first Fast Load."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "streamlit_app.py"
text = APP.read_text(encoding="utf-8")
changes = 0


def replace_once(old: str, new: str, label: str, optional: bool = False) -> None:
    global text, changes
    if old not in text:
        if optional:
            print(f"SKIP (optional): {label}")
            return
        raise SystemExit(f"MISSING: {label}")
    text = text.replace(old, new, 1)
    changes += 1
    print(f"OK: {label}")


for fn in (
    "fetch_completed_games_recent",
    "build_first_round_series_cached",
    "build_second_round_series_cached",
    "build_conference_finals_series_cached",
    "build_nba_finals_series_cached",
    "get_team_context_cached",
):
    old_dec = f"@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC)\ndef {fn}"
    new_dec = f"@st.cache_data(ttl=PLAYOFF_STATE_CACHE_TTL_SEC, show_spinner=False)\ndef {fn}"
    if old_dec in text:
        text = text.replace(old_dec, new_dec, 1)
        changes += 1
        print(f"OK: show_spinner {fn}")

replace_once(
    "    if _validation_mode_active() and not d_api and d_demo:\n"
    "        return _get_validation_playoff_state()\n"
    "    return get_playoff_state_cached(use_demo_backup, api_refresh)",
    "    if _qa_skip_expensive_apis():\n"
    "        return _build_static_playoff_state_fast()\n"
    "    if _validation_mode_active() and not d_api and d_demo:\n"
    "        return _get_validation_playoff_state()\n"
    "    return get_playoff_state_cached(use_demo_backup, api_refresh)",
    "get_merged static guard",
)

replace_once(
    'def _sidebar_team_label(team_name, stt=None):\n'
    '    """Mark eliminated teams so offseason Home sections are easy to find in the picker."""\n'
    "    try:\n"
    '        if get_team_playoff_status(team_name, stt).get("status") == "eliminated":\n'
    '            return f"📋 {team_name} (offseason outlook)"\n'
    "    except Exception:\n"
    "        if _is_home_eliminated(team_name):\n"
    '            return f"📋 {team_name} (offseason outlook)"\n'
    "    return team_name",
    'def _sidebar_team_label(team_name, stt=None):\n'
    '    """Mark eliminated teams — static profile only during Fast Load (no bracket engine)."""\n'
    "    if _validation_mode_active():\n"
    "        return team_name\n"
    "    if stt is not None:\n"
    "        try:\n"
    '            if get_team_playoff_status(team_name, stt).get("status") == "eliminated":\n'
    '                return f"📋 {team_name} (offseason outlook)"\n'
    "        except Exception:\n"
    "            pass\n"
    "        return team_name\n"
    "    p = TEAM_PROFILES.get(team_name) or {}\n"
    '    stt_static = str(p.get("status") or "").strip().lower()\n'
    '    if p.get("status") == "Eliminated" or "eliminat" in stt_static:\n'
    '        return f"📋 {team_name} (offseason outlook)"\n'
    "    return team_name",
    "_sidebar_team_label lightweight",
)

replace_once(
    "    try:\n"
    '        if get_team_playoff_status(team_name).get("status") == "eliminated":\n'
    "            return True\n"
    "    except Exception:\n"
    "        pass\n"
    "    if _dynamic_playoff_eliminated(team_name):\n"
    "        return True",
    "    if not _validation_mode_active():\n"
    "        try:\n"
    '            if get_team_playoff_status(team_name).get("status") == "eliminated":\n'
    "                return True\n"
    "        except Exception:\n"
    "            pass\n"
    "        if _dynamic_playoff_eliminated(team_name):\n"
    "            return True",
    "_is_home_eliminated fast guard",
)

replace_once(
    "    try:\n"
    "        from suite_workspace import init_suite_workspace\n"
    "\n"
    "        init_suite_workspace(st)\n"
    "    except Exception:\n"
    "        pass\n"
    "\n"
    "    try:\n"
    "        from suite_resume_launch import apply_suite_resume_launch",
    "    try:\n"
    "        from suite_workspace import init_suite_workspace\n"
    "\n"
    "        init_suite_workspace(st)\n"
    "    except Exception:\n"
    "        pass\n"
    "\n"
    "    try:\n"
    "        from nba_startup import ensure_fast_load_defaults\n"
    "\n"
    "        ensure_fast_load_defaults(st)\n"
    "    except Exception:\n"
    "        pass\n"
    "\n"
    "    try:\n"
    "        from suite_resume_launch import apply_suite_resume_launch",
    "ensure fast load defaults",
)

replace_once(
    "        restore_nba_disk_shell(st)\n"
    "        _sync_validation_mode_globals()\n"
    "        if should_defer_heavy_startup(st):\n"
    "            mark_deferred_workspace_sync(st)\n"
    "        else:\n"
    "            nba_restored = prepare_nba_workspace(st)",
    "        restore_nba_disk_shell(st)\n"
    "        _sync_validation_mode_globals()\n"
    "        mark_deferred_workspace_sync(st)",
    "always defer cloud before shell",
)

# Move load-speed toggles before team selector
replace_once(
    "    team_keys_sorted = sorted(TEAM_PROFILES.keys())\n"
    "\n"
    "    _restore_team = st.session_state.pop(\"_nba_restore_team\", None)",
    "    team_keys_sorted = sorted(TEAM_PROFILES.keys())\n"
    "\n"
    "    st.sidebar.markdown(\"### Load speed\")\n"
    "    st.sidebar.caption(\"Use fast load while testing workspace profiles or slow networks.\")\n"
    "    QA_MODE = st.sidebar.toggle(\n"
    "        \"Fast load\",\n"
    "        value=bool(st.session_state.get(\"QA_MODE\", False)),\n"
    "        key=\"QA_MODE\",\n"
    "        help=\"Skips heavy NBA API calls, bracket sync, autorefresh, and defers expensive page sections.\",\n"
    "    )\n"
    "    ULTRA_FAST_VALIDATION_MODE = st.sidebar.toggle(\n"
    "        \"Lite mode (no network)\",\n"
    "        value=bool(st.session_state.get(\"ULTRA_FAST_VALIDATION_MODE\", False)),\n"
    "        key=\"ULTRA_FAST_VALIDATION_MODE\",\n"
    "        help=\"Fastest startup: demo snapshots and placeholders only — no live API, CDN, or Plotly.\",\n"
    "    )\n"
    "    _sync_validation_mode_globals()\n"
    "    if _validation_mode_active():\n"
    "        _render_validation_mode_banner()\n"
    "\n"
    "    _restore_team = st.session_state.pop(\"_nba_restore_team\", None)",
    "toggles before team",
)

# Remove old toggles block after team change handler
replace_once(
    "    st.sidebar.markdown(\"### Load speed\")\n"
    "    st.sidebar.caption(\"Use fast load while testing workspace profiles or slow networks.\")\n"
    "    QA_MODE = st.sidebar.toggle(\n"
    "        \"Fast load\",\n"
    "        value=bool(st.session_state.get(\"QA_MODE\", False)),\n"
    "        key=\"QA_MODE\",\n"
    "        help=\"Skips heavy NBA API calls, bracket sync, autorefresh, and defers expensive page sections.\",\n"
    "    )\n"
    "    ULTRA_FAST_VALIDATION_MODE = st.sidebar.toggle(\n"
    "        \"Lite mode (no network)\",\n"
    "        value=bool(st.session_state.get(\"ULTRA_FAST_VALIDATION_MODE\", False)),\n"
    "        key=\"ULTRA_FAST_VALIDATION_MODE\",\n"
    "        help=\"Fastest startup: demo snapshots and placeholders only — no live API, CDN, or Plotly.\",\n"
    "    )\n"
    "    _sync_validation_mode_globals()\n"
    "    if _validation_mode_active():\n"
    "        _render_validation_mode_banner()\n"
    "    elif pp.is_demo_mode(st):",
    "    if pp.is_demo_mode(st):",
    "remove duplicate toggles",
)

replace_once(
    "    page = pages[page_label]\n"
    "    mark_startup_phase(st, \"sidebar\", boot_t0)",
    "    page = pages[page_label]\n"
    "    mark_startup_phase(st, \"sidebar\", boot_t0)\n"
    "    try:\n"
    "        from nba_startup import mark_shell_usable\n"
    "\n"
    "        mark_shell_usable(st, boot_t0)\n"
    "    except Exception:\n"
    "        pass",
    "shell usable marker",
    optional=True,
)

OLD_PAGE = """    if page in playoff_auto_refresh_pages:
        tick_playoff_state_autorefresh(page.replace(" ", "_").lower())

    from suite_analytical_question import render_suite_applied_math_insight

    render_suite_applied_math_insight(st, source_app="nba", source_page=page)

    if page == "Home Dashboard":
        render_playoff_command_center(favorite_team)"""

NEW_PAGE = """    if page in playoff_auto_refresh_pages:
        tick_playoff_state_autorefresh(page.replace(" ", "_").lower())

    _skip_heavy_page = False
    try:
        from nba_startup import should_skip_page_heavy_body

        _skip_heavy_page = should_skip_page_heavy_body(st, page)
    except Exception:
        _skip_heavy_page = _validation_mode_active() and _validation_page_deferred(page)

    if not _validation_mode_active():
        from suite_analytical_question import render_suite_applied_math_insight

        render_suite_applied_math_insight(st, source_app="nba", source_page=page)

    if _skip_heavy_page:
        try:
            from nba_startup import render_fast_load_page_placeholder

            render_fast_load_page_placeholder(st, page, favorite_team)
        except Exception:
            st.info(f"Fast load — {page} placeholder. Load full content when ready.")
    elif page == "Home Dashboard":
        render_playoff_command_center(favorite_team)"""

replace_once(OLD_PAGE, NEW_PAGE, "page routing defer", optional=True)

replace_once(
    "    if pop_deferred_workspace_sync(st):\n"
    "        defer_t0 = pytime.perf_counter()\n"
    "        try:\n"
    "            from nba_persistent_state import prepare_nba_workspace\n"
    "\n"
    "            prepare_nba_workspace(st)\n"
    "        except Exception:\n"
    "            pass\n"
    "        try:\n"
    "            from nba_startup import record_startup_section\n"
    "\n"
    "            record_startup_section(st, \"restore\", (pytime.perf_counter() - defer_t0) * 1000.0)\n"
    "        except Exception:\n"
    "            pass",
    "    if pop_deferred_workspace_sync(st) and not should_defer_heavy_startup(st):\n"
    "        defer_t0 = pytime.perf_counter()\n"
    "        try:\n"
    "            from nba_persistent_state import prepare_nba_workspace\n"
    "\n"
    "            prepare_nba_workspace(st)\n"
    "        except Exception:\n"
    "            pass\n"
    "        try:\n"
    "            from nba_startup import record_startup_section\n"
    "\n"
    "            record_startup_section(st, \"cloud_sync\", (pytime.perf_counter() - defer_t0) * 1000.0)\n"
    "        except Exception:\n"
    "            pass",
    "cloud sync only when fast load off",
    optional=True,
)

# Skip AMI sidebar entry in fast load
replace_once(
    "    render_applied_math_sidebar_entry(\n"
    "        st,\n"
    "        source_app=\"nba\",\n"
    "        source_page=_nba_ami_page,\n"
    "        session_state=st.session_state,\n"
    "        developer_mode=can_show_developer_tools(st=st),\n"
    "        context_extra_builder=(\n"
    "            (lambda: {\"team\": favorite_team, \"page\": _nba_ami_page, \"fast_load\": True})\n"
    "            if _validation_mode_active()\n"
    "            else (\n"
    "                lambda: build_nba_applied_math_context(_nba_ami_page, st.session_state)\n"
    "                if build_nba_applied_math_context\n"
    "                else {\"team\": favorite_team, \"page\": _nba_ami_page}\n"
    "            )\n"
    "        ),\n"
    "        source_state_builder=(\n"
    "            lambda: build_source_state(_nba_ami_page, st.session_state)\n"
    "            if build_source_state\n"
    "            else None\n"
    "        ),\n"
    "    )",
    "    if not _validation_mode_active():\n"
    "        render_applied_math_sidebar_entry(\n"
    "            st,\n"
    "            source_app=\"nba\",\n"
    "            source_page=_nba_ami_page,\n"
    "            session_state=st.session_state,\n"
    "            developer_mode=can_show_developer_tools(st=st),\n"
    "            context_extra_builder=(\n"
    "                lambda: build_nba_applied_math_context(_nba_ami_page, st.session_state)\n"
    "                if build_nba_applied_math_context\n"
    "                else {\"team\": favorite_team, \"page\": _nba_ami_page}\n"
    "            ),\n"
    "            source_state_builder=(\n"
    "                lambda: build_source_state(_nba_ami_page, st.session_state)\n"
    "                if build_source_state\n"
    "                else None\n"
    "            ),\n"
    "        )",
    "skip AMI sidebar in fast load",
    optional=True,
)

APP.write_text(text, encoding="utf-8")
print(f"Done — {changes} replacements")
