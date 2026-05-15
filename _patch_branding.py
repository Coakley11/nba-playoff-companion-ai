from pathlib import Path

p = Path("streamlit_app.py")
t = p.read_text(encoding="utf-8")

replacements = [
    # MI momentum pill block
    (
        '        extra = ""\n        if num == "8":',
        '        mom_pill = ""\n        if kind == "momentum" and tone in ("up", "down", "flat"):\n'
        '            lbl = {"up": "Swing up", "down": "Swing down", "flat": "Flat"}.get(tone, "")\n'
        '            mom_pill = f\'<span class="mi-mom-pill {tone}">{lbl}</span>\'\n'
        '        extra = ""\n        if num == "8":',
    ),
    (
        'f"<motion class=\'mi-title\'>{safe_title}</motion><motion class=\'mi-body\'>{b}</motion>{extra}</motion>",',
        'f"<motion class=\'mi-title\'>{safe_title}{mom_pill}</motion><motion class=\'mi-body\'>{b}</motion>{extra}</motion>",',
    ),
    (
        "def bracket_series_card(s, round_display_name, show_round_chip=False):",
        "def bracket_series_card(s, round_display_name, show_round_chip=False, favorite_team=None):",
    ),
    (
        '    card_mod = "bmk-card--active" if active else "bmk-card--complete"',
        '    card_mod = "bmk-card--active" if active else "bmk-card--complete"\n'
        '    if favorite_team and favorite_team in (a, b):\n'
        '        card_mod += " bmk-card--yours"',
    ),
    (
        '        classes = ["bmk-team"]\n        if is_winner:',
        '        classes = ["bmk-team"]\n        if favorite_team and team == favorite_team:\n'
        '            classes.append("bmk-team--yours")\n        if is_winner:',
    ),
    ("def render_bracket():", "def render_bracket(favorite_team=None):"),
    (
        'east_fr_cards = "".join(bracket_series_card(s, "First Round") for s in east_fr)',
        'east_fr_cards = "".join(bracket_series_card(s, "First Round", favorite_team=favorite_team) for s in east_fr)',
    ),
    (
        'east_sr_cards = "".join(bracket_series_card(s, "Conference Semifinals") for s in east_sr)',
        'east_sr_cards = "".join(bracket_series_card(s, "Conference Semifinals", favorite_team=favorite_team) for s in east_sr)',
    ),
    (
        'west_sr_cards = "".join(bracket_series_card(s, "Conference Semifinals") for s in west_sr)',
        'west_sr_cards = "".join(bracket_series_card(s, "Conference Semifinals", favorite_team=favorite_team) for s in west_sr)',
    ),
    (
        'west_fr_cards = "".join(bracket_series_card(s, "First Round") for s in west_fr)',
        'west_fr_cards = "".join(bracket_series_card(s, "First Round", favorite_team=favorite_team) for s in west_fr)',
    ),
    (
        'east_cf_block = bracket_series_card(list(east_conf.values())[0], "Conference Finals")',
        'east_cf_block = bracket_series_card(list(east_conf.values())[0], "Conference Finals", favorite_team=favorite_team)',
    ),
    (
        'west_cf_block = bracket_series_card(list(west_conf.values())[0], "Conference Finals")',
        'west_cf_block = bracket_series_card(list(west_conf.values())[0], "Conference Finals", favorite_team=favorite_team)',
    ),
    (
        'finals_block = bracket_series_card(list(finals.values())[0], "NBA Finals")',
        'finals_block = bracket_series_card(list(finals.values())[0], "NBA Finals", favorite_team=favorite_team)',
    ),
    ("    render_bracket()", "    render_bracket(favorite_team)"),
    (
        '    st.markdown("#### Home Dashboard")',
        '    render_fan_page_hero(team_name, f"{fan_nick(team_name)} Home Dashboard", '
        '"Series snapshot, injuries, stars, and offseason outlook when the run is over.", "YOUR TEAM")',
    ),
    (
        '    st.markdown("### 🏟️ Live Game Center")',
        '    render_fan_page_hero(favorite_team, "Live Game Center", '
        'f"Real-time board for {fan_nick(favorite_team)}.", "LIVE HUB")',
    ),
    (
        '    st.subheader("Playoff Path So Far")',
        '    render_fan_page_hero(team_name, "Playoff path so far", '
        '"Every round you played — scores, MVPs, and series results.", "PLAYOFF HISTORY")\n'
        '    team_section_header("Round-by-round results", "📜")',
    ),
    (
        'f"<motion class=\'mi-title\'>{safe_title}</motion><motion class=\'mi-body\'>{b}</motion>{extra}</motion>",',
        'f"<motion class=\'mi-title\'>{safe_title}{mom_pill}</motion><motion class=\'mi-body\'>{b}</motion>{extra}</motion>",',
    ),
]

# Fix div in replacements - use actual div from file
d = "div"
fixed = []
for old, new in replacements:
    old = old.replace("<motion", f"<{d}").replace("</motion>", f"</{d}>")
    new = new.replace("<motion", f"<{d}").replace("</motion>", f"</{d}>")
    fixed.append((old, new))

for old, new in fixed:
    if old not in t:
        print("MISSING:", old[:60])
        continue
    t = t.replace(old, new, 1)
    print("OK:", old[:50])

# live score banner insertion
marker = '    st.markdown("#### Game row (minimal)")'
if marker in t and "render_live_score_banner" not in t.split(marker)[0][-800:]:
    block = """    render_live_score_banner(favorite_team, away_tri, home_tri, away_score, home_score, status, phase)
    team_section_header("Game details", "🏟️")
"""
    t = t.replace(marker, block + marker)
    t = t.replace(
        '    st.write(f"**{away_name}** @ **{home_name}**")\n    st.metric("Score", f"{away_tri} {away_score}  —  {home_tri} {home_score}")\n',
        "",
    )

p.write_text(t, encoding="utf-8")
print("done")
