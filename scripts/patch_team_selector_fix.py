from pathlib import Path

p = Path(__file__).resolve().parent.parent / "streamlit_app.py"
text = p.read_text(encoding="utf-8")

old = """    _restore_team = st.session_state.pop("_nba_restore_team", None)
    if _restore_team and _restore_team in team_keys_sorted:
        st.session_state[NBA_TEAM_SELECT_KEY] = _restore_team
        st.session_state["favorite_team"] = _restore_team
    elif NBA_TEAM_SELECT_KEY not in st.session_state:
        _saved_team = st.session_state.get("favorite_team")
        if _saved_team in team_keys_sorted:
            st.session_state[NBA_TEAM_SELECT_KEY] = _saved_team
        elif not nba_restored and "_nba_restore_error" not in st.session_state:
            try:
                from suite_workspace import DEFAULT_WORKSPACE_ID, get_active_workspace_id

                _ws_default = get_active_workspace_id(st)
            except Exception:
                _ws_default = "daniel"
            if _ws_default in (DEFAULT_WORKSPACE_ID, "daniel"):
                _fallback_team = (
                    "New York Knicks" if "New York Knicks" in team_keys_sorted else team_keys_sorted[0]
                )
            else:
                _fallback_team = team_keys_sorted[0]
            st.session_state[NBA_TEAM_SELECT_KEY] = _fallback_team"""

new = """    try:
        from nba_persistent_state import init_nba_team_selector_state

        init_nba_team_selector_state(st, team_keys_sorted, nba_restored=nba_restored)
    except Exception:
        pass"""

if old not in text:
    raise SystemExit("team init block not found")
p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("patched streamlit_app team init")
