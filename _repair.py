from pathlib import Path

p = Path(__file__).with_name("streamlit_app.py")
t = p.read_text(encoding="utf-8")

# 1. create_boxscore_df corruption
t = t.replace(
    "    return pd.DataFrame(rows)    render_fan_section_close()",
    "    return pd.DataFrame(rows)",
    1,
)

# 2. stray close before sidebar helper
t = t.replace(
    "\n    render_fan_section_close()\n\ndef _sidebar_team_label",
    "\ndef _sidebar_team_label",
    1,
)

# 3. team history page — replace corrupted block
start = t.find("    st.markdown(\"if render_fan_section(\"Franchise legends overview\"")
end = t.find("\n\n# ==========================================================\n# Sidebar", start)
if start > 0 and end > start:
    fixed = '''    if render_fan_section("Franchise legends overview", "🏆", caption="Top franchise playoff icons on the curated board.", tone="default"):
        render_fan_section_open()
    st.markdown("<motion class='hist-grid'>" + "".join(_history_card_html(team_name, p, current=(_is_current_history_player(p["name"], current_names) or p.get("current_watch"))) for p in legends[:10]) + "</div>", unsafe_allow_html=True)
    render_fan_section_close()

    if render_fan_section("Franchise playoff leaders", "📊", caption="Sortable leaderboard from curated history data.", tone="default"):
        render_fan_section_open()
    df = _history_table_df(legends, current_names)
    sort_label = st.selectbox("Sort leaderboard by", ["Total playoff points", "Playoff points per game", "Rebounds", "Assists", "Steals", "Blocks", "Three-pointers", "40-point playoff games", "30-point playoff games", "Playoff games played", "Finals appearances", "Championships"], key=f"history_sort_{team_name}")
    show_df = df.sort_values(_history_sort_col(sort_label), ascending=False).reset_index(drop=True)
    render_fan_stat_table(show_df, team_name)
    render_fan_section_close()

    if render_fan_section("Current players climbing the list", "📈", caption="Roster names chasing franchise milestones.", tone="default"):
        render_fan_section_open()
    if current_entries:
        st.markdown("<div class='hist-grid'>" + "".join(_history_card_html(team_name, p, current=True) for p in current_entries) + "</div>", unsafe_allow_html=True)
    else:
        st.info("No current roster player is on this curated top board yet. A deep run is how someone starts forcing their way onto it.")
    render_fan_section_close()

    if render_fan_section("Chase / projection storylines", "🎯", caption="Milestone paths for active players.", tone="default"):
        render_fan_section_open()
    if current_entries:
        for p in current_entries:
            st.markdown(f"**{p['name']} history watch**")
            milestone_html = []
            for label, text, progress in _milestone_lines_for_player(p, legends):
                milestone_html.append(f"<div class='hist-milestone'><b>{html.escape(label.title())}</b><br><span style='font-size:12px;color:#475569'>{html.escape(text)}</span><motion class='hist-progress'><span style='width:{max(5, min(98, progress * 100)):.0f}%'></span></div></div>")
            st.markdown("<div class='hist-milestone-grid'>" + "".join(milestone_html) + "</div>", unsafe_allow_html=True)
    else:
        st.caption("Milestone cards appear when a current player is on the franchise board.")
    render_fan_section_close()

    if render_fan_section("Player comparison cards", "⚖️", caption="Side-by-side legend vs current comparisons.", tone="default"):
        render_fan_section_open()
    cards = []
    by_name = {p["name"]: p for p in legends}
    for cur in current_entries[:3]:
        targets = [by_name[n] for n in cur.get("compare_to", []) if n in by_name] or [p for p in legends[:4] if p["name"] != cur["name"]]
        for target in targets[:2]:
            cards.append(_comparison_card_html(cur, target))
    if cards:
        st.markdown("<div class='hist-compare-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)
    else:
        st.caption("Comparison cards appear when a current player is part of the curated history board.")
    render_fan_section_close()

    if render_fan_section("Milestones within reach", "🏁", caption="What is still on the table this run.", tone="default"):
        render_fan_section_open()
    if current_entries:
        rows = []
        for cur in current_entries:
            for label, text, _progress in _milestone_lines_for_player(cur, legends):
                rows.append({"Player": cur["name"], "Milestone": label.title(), "What is within reach": text, "Data type": "Curated estimate"})
        render_fan_stat_table(pd.DataFrame(rows), team_name)
    else:
        st.info("No current-player milestones yet for this team board.")
    render_fan_section_close()

'''
    fixed = fixed.replace("<motion class='hist-grid'>", "<div class='hist-grid'>")
    fixed = fixed.replace('</motion>", unsafe_allow_html=True)', '</motion>", unsafe_allow_html=True)'.replace("</motion>", "</div>"))
    fixed = fixed.replace("<motion class='hist-progress'>", "<div class='hist-progress'>")
    fixed = fixed.replace("</div></div>", "</div></div>")  # milestone line already ok
    # fix milestone broken tag
    fixed = fixed.replace(
        'milestone_html.append(f"<div class=\'hist-milestone\'><b>{html.escape(label.title())}</b><br><span style=\'font-size:12px;color:#475569\'>{html.escape(text)}</span><motion class=\'hist-progress\'><span style=\'width:{max(5, min(98, progress * 100)):.0f}%\'></span></motion></motion>")',
        'milestone_html.append(f"<div class=\'hist-milestone\'><b>{html.escape(label.title())}</b><br><span style=\'font-size:12px;color:#475569\'>{html.escape(text)}</span><div class=\'hist-progress\'><span style=\'width:{max(5, min(98, progress * 100)):.0f}%\'></span></div></div>")',
    )
    t = t[:start] + fixed + t[end:]

# 4. Player hub — revert to team_section_header
import re

def revert_player_hub(text):
    m = re.search(r"(    # --- 1 · Current run ---\n)(.*?)(    return pd\.DataFrame\(rows\))", text, re.S)
    if not m:
        return text
    # find function end differently
    fn_start = text.find("    # --- 1 · Current run ---")
    fn_end = text.find("\ndef create_boxscore_df", fn_start)
    if fn_start < 0 or fn_end < 0:
        return text
    block = text[fn_start:fn_end]
    if "if render_fan_section(\"1 · Current playoff run\"" not in block:
        return text
    block = re.sub(
        r"    if render_fan_section\([^\n]+\n        render_fan_section_open\(\)\n",
        "    team_section_header(",
        block,
    )
    block = re.sub(
        r'    if render_fan_section\("([^"]+)", "([^"]+)", caption="[^"]*", tone="default"\):\n        render_fan_section_open\(\)\n',
        r'    team_section_header("\1", "\2")\n',
        block,
    )
    block = re.sub(r"\n        render_fan_section_close\(\)\n", "\n", block)
    block = block.replace("    render_fan_section_close()\n", "")
    return text[:fn_start] + block + text[fn_end:]

t = revert_player_hub(t)

# 5. Home dashboard — fix bad indents on close lines
for bad in [
    "    sections.append(\"series_board\")\n        render_fan_section_close()",
    "    sections.append(\"runway\")\n        render_fan_section_close()",
    "    sections.append(\"fast_series_snapshot\")\n        render_fan_section_close()",
]:
    good = bad.replace("\n        render_fan_section_close()", "\n    render_fan_section_close()")
    t = t.replace(bad, good, 1)

# section 1: close should be after series_board without extra indent issue - already fixed above

# section 5 close only once at end of injury block - remove duplicate inside else
t = t.replace(
    """        sections.append("injury_snapshot_fast_placeholder")
        render_fan_section_close()

    def sec_injuries():""",
    """        sections.append("injury_snapshot_fast_placeholder")
    render_fan_section_close()

    def sec_injuries():""",
    1,
)

p.write_text(t, encoding="utf-8")
print("repair done")
