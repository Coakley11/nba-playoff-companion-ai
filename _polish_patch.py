from pathlib import Path
import re

p = Path(__file__).with_name("streamlit_app.py")
t = p.read_text(encoding="utf-8")

# Remove duplicate badge assignment block in render_home_current_game_card
t2 = re.sub(
    r"    badge = badge\.replace\(\"motion\", \"motion\"\).*?\n    else:\n        badge = \"\"\n    st\.markdown\(\n        f\"\"\"\n<div class=\"\{tone\}\">",
    '    st.markdown(\n        f"""\n<div class="{tone}">\n  {badge}',
    t,
    count=1,
    flags=re.S,
)
if t2 == t:
    t2 = re.sub(
        r"    badge = badge\.replace\(\"motion\", \"div\"\).*?\n    else:\n        badge = \"\"\n    st\.markdown\(\n        f\"\"\"\n<div class=\"\{tone\}\">",
        '    st.markdown(\n        f"""\n<div class="{tone}">\n  {badge}',
        t,
        count=1,
        flags=re.S,
    )
t = t2

# Fix motion typos globally in HTML strings
t = t.replace('<motion class="home-live-strip-sub">', '<div class="home-live-strip-sub">')
t = t.replace('<motion class="home-live-badge">', '<motion class="home-live-badge">')
t = t.replace('<div class="home-live-badge">', '<div class="home-live-badge">')

# Hub strip
if 'badge = ""\n        if phase == "live":' not in t:
    t = t.replace(
        '        if phase == "live":\n'
        '            mod = "home-live-strip home-live-strip--live"\n'
        '            title = "🔴 LIVE NOW · Game in progress"\n'
        '        elif phase == "pregame" and soon:\n'
        '            mod = "home-live-strip home-live-strip--soon"\n'
        '            title = "⏳ GAME STARTING SOON"\n',
        '        badge = ""\n'
        '        if phase == "live":\n'
        '            mod = "home-live-strip home-live-strip--live"\n'
        '            title = "🔴 LIVE NOW · Game in progress"\n'
        '            badge = \'<motion class="home-live-badge">ON AIR · LIVE</div>\'\n'
        '        elif phase == "pregame" and soon:\n'
        '            mod = "home-live-strip home-live-strip--soon"\n'
        '            title = "⏳ GAME STARTING SOON"\n'
        '            badge = \'<div class="home-live-badge">TIPOFF SOON</div>\'\n',
        1,
    )
    t = t.replace(
        '<div class="{mod}">\n  <div class="home-live-strip-title">{title}</div>',
        '<div class="{mod}">\n  {badge}\n  <div class="home-live-strip-title">{title}</div>',
        1,
    )

# _live_gc_section
old = '''def _live_gc_section(title, icon, fn, *args, **kwargs):
    """Render a Live GC block; failures stay local."""
    team_section_header(title, icon)
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        st.caption(f"{title} could not load right now ({exc}).")'''
new = '''def _live_gc_section(title, icon, fn, *args, **kwargs):
    """Render a Live GC block; failures stay local."""
    if not render_fan_section(title, icon, tone="broadcast"):
        return
    render_fan_section_open()
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        st.caption(f"{title} could not load right now ({exc}).")
    render_fan_section_close()'''
if old in t:
    t = t.replace(old, new, 1)

# Previous rounds
if 'team_section_header("Round-by-round results"' in t:
    t = t.replace(
        '    team_section_header("Round-by-round results", "📜")\n',
        '    if render_fan_section("Round-by-round results", "📜", caption="Every series you played this postseason."):\n        render_fan_section_open()\n',
        1,
    )
    anchor = '# Fail-safe Live Game Center override'
    if anchor in t and 'render_fan_section_close()' not in t.split('def render_previous_rounds_history')[1].split(anchor)[0]:
        t = t.replace(
            '            render_series_history_card(team_name, opp, games, round_label, note)\n\n\n' + anchor,
            '            render_series_history_card(team_name, opp, games, round_label, note)\n    render_fan_section_close()\n\n\n' + anchor,
            1,
        )

# Live GC performers sections
for title, icon in [
    ("Top performers", "⭐"),
    ("Lineups / on-court estimate", "📋"),
    ("Pregame command board", "⏳"),
]:
    t = t.replace(
        f'    team_section_header("{title}", "{icon}")\n',
        f'    if render_fan_section("{title}", "{icon}", tone="broadcast"):\n        render_fan_section_open()\n',
        1,
    )

p.write_text(t, encoding="utf-8")
print("ok")
