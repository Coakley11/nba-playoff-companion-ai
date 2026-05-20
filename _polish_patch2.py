from pathlib import Path

p = Path(__file__).with_name("streamlit_app.py")
t = p.read_text(encoding="utf-8")

# Home dashboard sections
t = t.replace(
    """    sec1_title = "1 · How the run ended" if is_eliminated else "1 · Where the series stands"
    st.markdown(f'<div class="cmd-sec">{html.escape(sec1_title)}</div>', unsafe_allow_html=True)
    snap_cols = st.columns(4)""",
    """    sec1_title = "1 · How the run ended" if is_eliminated else "1 · Where the series stands"
    if render_fan_section(
        sec1_title,
        "📊",
        caption="Playoff mood, seed, and the game log for this chapter.",
        tone="elim" if is_eliminated else "default",
    ):
        render_fan_section_open()
    snap_cols = st.columns(4)""",
    1,
)

t = t.replace(
    """    sections.append("series_board")

    st.markdown("<motion class='cmd-sec'>2 · Tonight's runway</div>", unsafe_allow_html=True)""",
    """    sections.append("series_board")
        render_fan_section_close()

    if render_fan_section(
        "2 · Tonight's runway",
        "🛫",
        caption="Next tip, opponent, and live runway.",
        tone="soon" if effective_live else "default",
    ):
        render_fan_section_open()""",
    1,
)
if "cmd-sec'>2 · Tonight's runway</motion>" not in t:
    t = t.replace(
        """    sections.append("series_board")

    st.markdown("<div class='cmd-sec'>2 · Tonight's runway</div>", unsafe_allow_html=True)""",
        """    sections.append("series_board")
        render_fan_section_close()

    if render_fan_section(
        "2 · Tonight's runway",
        "🛫",
        caption="Next tip, opponent, and live runway.",
        tone="soon" if effective_live else "default",
    ):
        render_fan_section_open()""",
        1,
    )

t = t.replace(
    """    sections.append("runway")

    st.markdown('<div class="cmd-sec">3 · What it feels like</div>', unsafe_allow_html=True)
    render_team_outlook(team_name, compact_home=True, series_obj=current_series_obj)
    sections.append("outlook_compact")

    sec4_title = "4 · Next-round lens" if hctx.get("advanced") else "4 · Series at a glance"
    st.markdown(f'<div class="cmd-sec">{html.escape(sec4_title)}</motion>', unsafe_allow_html=True)""",
    """    sections.append("runway")
        render_fan_section_close()

    if render_fan_section("3 · What it feels like", "🎙️", caption="Short broadcast read on the series.", tone="default"):
        render_fan_section_open()
    render_team_outlook(team_name, compact_home=True, series_obj=current_series_obj)
    sections.append("outlook_compact")
        render_fan_section_close()

    sec4_title = "4 · Next-round lens" if hctx.get("advanced") else "4 · Series at a glance"
    if render_fan_section(sec4_title, "🔭", caption="Opponent, series score, and latest game.", tone="default"):
        render_fan_section_open()""",
    1,
)
if 'sec4_title)}</motion>' not in t:
    t = t.replace(
        """    sections.append("runway")

    st.markdown('<div class="cmd-sec">3 · What it feels like</div>', unsafe_allow_html=True)
    render_team_outlook(team_name, compact_home=True, series_obj=current_series_obj)
    sections.append("outlook_compact")

    sec4_title = "4 · Next-round lens" if hctx.get("advanced") else "4 · Series at a glance"
    st.markdown(f'<div class="cmd-sec">{html.escape(sec4_title)}</div>', unsafe_allow_html=True)""",
        """    sections.append("runway")
        render_fan_section_close()

    if render_fan_section("3 · What it feels like", "🎙️", caption="Short broadcast read on the series.", tone="default"):
        render_fan_section_open()
        render_team_outlook(team_name, compact_home=True, series_obj=current_series_obj)
        sections.append("outlook_compact")
        render_fan_section_close()

    sec4_title = "4 · Next-round lens" if hctx.get("advanced") else "4 · Series at a glance"
    if render_fan_section(sec4_title, "🔭", caption="Opponent, series score, and latest game.", tone="default"):
        render_fan_section_open()""",
        1,
    )

t = t.replace(
    """    sections.append("fast_series_snapshot")

    st.markdown("<div class='cmd-sec'>5 · Who's available</div>", unsafe_allow_html=True)""",
    """    sections.append("fast_series_snapshot")
        render_fan_section_close()

    if render_fan_section("5 · Who's available", "🩹", caption="Injury snapshot when live mode is on.", tone="default"):
        render_fan_section_open()""",
    1,
)

t = t.replace(
    """        sections.append("injury_snapshot_fast_placeholder")

    def sec_injuries():""",
    """        sections.append("injury_snapshot_fast_placeholder")
        render_fan_section_close()

    def sec_injuries():""",
    1,
)

# Player hub: auto-close between team_section_header calls
import re

def wrap_player_sections(text):
    parts = text.split("def render_player_playoff_story_hub")
    if len(parts) < 2:
        return text
    head, rest = parts[0], parts[1]
    end = rest.find("\n\ndef ")
    if end < 0:
        return text
    body, tail = rest[:end], rest[end:]
    markers = list(re.finditer(r'    team_section_header\("([^"]+)", "([^"]+)"\)\n', body))
    if not markers:
        return text
    out = []
    last = 0
    for i, m in enumerate(markers):
        out.append(body[last : m.start()])
        title, icon = m.group(1), m.group(2)
        if i > 0:
            out.append("        render_fan_section_close()\n\n")
        cap = {
            "1 · Current playoff run": "Box score line for this postseason.",
            "2 · Series-by-series breakdown": "Each opponent chunk in playoff order.",
            "3 · Pressure & legacy": "Pressure meters and legacy stakes.",
            "4 · Historical comparison engine": "Franchise and peer comparisons.",
            "5 · Clutch impact": "Takeover games and late-game proxies.",
            "6 · Narrative storylines": "Story beats from the log.",
            "7 · Progression & raw log": "Charts and full game log.",
        }.get(title, "")
        out.append(
            f'    if render_fan_section("{title}", "{icon}", caption="{cap}", tone="default"):\n'
            f"        render_fan_section_open()\n"
        )
        last = m.end()
    out.append(body[last:])
    out.append("    render_fan_section_close()\n")
    return head + "def render_player_playoff_story_hub" + "".join(out) + tail

t = wrap_player_sections(t)

# Matchup lineups section header
t = t.replace(
    '    st.markdown("### Starting Lineup Matchups")',
    '    if render_fan_section("Starting lineup matchups", "📋", caption="Estimated playoff preview boards by position.", tone="default"):\n        render_fan_section_open()',
    1,
)
# close lineups before next function - find end of render_matchup_lineups_page
idx = t.find("def render_matchup_lineups_page")
if idx > 0:
    nxt = t.find("\ndef ", idx + 10)
    block = t[idx:nxt]
    if "render_fan_section_close()" not in block and "render_fan_section_open()" in block:
        # insert before return at end
        block2 = block.rstrip()
        if block2.endswith("return"):
            block2 = block2[:-6] + "    render_fan_section_close()\n    return"
            t = t[:idx] + block2 + t[nxt:]

# Team history
hist_map = [
    ("1 - Franchise Legends Overview", "Franchise legends overview", "🏆", "Top franchise playoff icons."),
    ("2 - Franchise Playoff Leaders", "Franchise playoff leaders", "📊", "Sortable curated leaderboard."),
    ("3 - Current Players Climbing the List", "Current players climbing", "📈", "Roster names on the chase board."),
    ("4 - Chase / Projection Storylines", "Chase storylines", "🎯", "Milestone paths for active players."),
    ("5 - Player Comparison Cards", "Player comparisons", "⚖️", "Legend vs current side-by-sides."),
    ("6 - Milestones Within Reach", "Milestones within reach", "🏁", "What is still on the table."),
]
for old, title, icon, cap in hist_map:
    old_div = f"<div class='hist-section'>{old}</div>"
    if old_div in t:
        t = t.replace(
            old_div,
            f'if render_fan_section("{title}", "{icon}", caption="{cap}", tone="default"):\n        render_fan_section_open()',
            1,
        )

# Close history sections before next header or end
for i in range(len(hist_map) - 1):
    _, t1, _, _ = hist_map[i]
    _, t2, _, _ = hist_map[i + 1]
    a = f'if render_fan_section("{t1}"'
    b = f'if render_fan_section("{t2}"'
    if a in t and b in t:
        pos_a = t.find(a)
        pos_b = t.find(b, pos_a + 1)
        mid = t[pos_a:pos_b]
        if "render_fan_section_close()" not in mid:
            t = t[:pos_b] + "        render_fan_section_close()\n\n    " + t[pos_b:]

if 'if render_fan_section("Milestones within reach"' in t:
    end_fn = t.find("\ndef ", t.find("def render_team_history_leaders_page"))
    last_sec = t.rfind('if render_fan_section("Milestones within reach"', 0, end_fn)
    if last_sec > 0 and "render_fan_section_close()" not in t[last_sec:end_fn]:
        t = t[:end_fn] + "    render_fan_section_close()\n" + t[end_fn:]

# MI loop wrap
mi_old = """        st.markdown(
            f"<div class='mi-card {cls}'><motion class='mi-num'>SECTION {num}</div>"
            f"<div class='mi-title'>{safe_title}{mom_pill}</div><div class='mi-body'>{b}</div>{extra}</div>",
            unsafe_allow_html=True,
        )"""
mi_old2 = mi_old.replace("motion", "motion")
for cand in [
    """        st.markdown(
            f"<div class='mi-card {cls}'><motion class='mi-num'>SECTION {num}</div>"
            f"<div class='mi-title'>{safe_title}{mom_pill}</div><div class='mi-body'>{b}</div>{extra}</motion>",
            unsafe_allow_html=True,
        )""",
    """        st.markdown(
            f"<div class='mi-card {cls}'><div class='mi-num'>SECTION {num}</div>"
            f"<motion class='mi-title'>{safe_title}{mom_pill}</motion><div class='mi-body'>{b}</div>{extra}</div>",
            unsafe_allow_html=True,
        )""",
    """        st.markdown(
            f"<motion class='mi-card {cls}'><div class='mi-num'>SECTION {num}</div>"
            f"<div class='mi-title'>{safe_title}{mom_pill}</div><div class='mi-body'>{b}</div>{extra}</div>",
            unsafe_allow_html=True,
        )""",
]:
    cand = cand.replace("motion", "div") if "motion class='mi-card'" in cand else cand
    cand = cand.replace("<motion class='mi-card", "<div class='mi-card").replace("</motion>", "</div>") if "mi-card" in cand and "motion" in cand else cand

mi_new = """        render_fan_section_header(title, icon, caption=f"Scouting slice {num}", tone="default")
        render_fan_section_open()
        st.markdown(
            f"<div class='mi-card {cls}'><div class='mi-num'>SECTION {num}</motion>"
            f"<div class='mi-title'>{safe_title}{mom_pill}</div><div class='mi-body'>{b}</div>{extra}</div>",
            unsafe_allow_html=True,
        )
        render_fan_section_close()"""
mi_new = mi_new.replace("</motion>", "</motion>").replace("<motion class='mi-num'>", "<div class='mi-num'>").replace("SECTION {num}</motion>", "SECTION {num}</motion>").replace("SECTION {num}</motion>", "SECTION {num}</div>")

# find actual mi markdown in file
import re as _re
m = _re.search(
    r"        st\.markdown\(\n            f\"<div class='mi-card \{cls\}'.*?unsafe_allow_html=True,\n        \)",
    t,
    _re.S,
)
if m and "render_fan_section_header(title, icon" not in m.group(0):
    t = t[: m.start()] + mi_new + t[m.end() :]

# Offseason reflection
t = t.replace(
    '    team_section_header("1 · Season reflection", "📋")\n    with st.container(border=True):',
    '    if render_fan_section("1 · Season reflection", "📋", caption="What worked and what ended the run.", tone="elim"):\n        render_fan_section_open()\n    with st.container(border=True):',
    1,
)

p.write_text(t, encoding="utf-8")
print("patch2 ok")
