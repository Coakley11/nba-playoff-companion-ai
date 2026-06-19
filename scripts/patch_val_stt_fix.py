from pathlib import Path

p = Path(__file__).resolve().parent.parent / "streamlit_app.py"
text = p.read_text(encoding="utf-8")
old = (
    "    _set_lgc_route_skip_bracket_api(page == \"Live Game Center\")\n"
    "    _lgc_stt = _get_lgc_local_playoff_state() if page == \"Live Game Center\" else None\n"
    "    profile = get_effective_team_profile(\n"
    "        favorite_team, _val_stt if _validation_mode_active() else _lgc_stt\n"
    "    )"
)
new = (
    "    _set_lgc_route_skip_bracket_api(page == \"Live Game Center\")\n"
    "    _lgc_stt = _get_lgc_local_playoff_state() if page == \"Live Game Center\" else None\n"
    "    _val_stt = _get_validation_playoff_state() if _validation_mode_active() else None\n"
    "    try:\n"
    "        from nba_startup import resolve_profile_playoff_state\n"
    "\n"
    "        _active_stt = resolve_profile_playoff_state(\n"
    "            validation_mode=_validation_mode_active(),\n"
    "            page=page,\n"
    "            validation_stt=_val_stt,\n"
    "            lgc_stt=_lgc_stt,\n"
    "        )\n"
    "    except Exception:\n"
    "        _active_stt = _val_stt if _validation_mode_active() else _lgc_stt\n"
    "    profile = get_effective_team_profile(favorite_team, _active_stt)"
)
if old not in text:
    raise SystemExit("OLD block not found")
p.write_text(text.replace(old, new, 1), encoding="utf-8")
print("patched ok")
