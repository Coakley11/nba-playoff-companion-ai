# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parent / "streamlit_app.py"
t = p.read_text(encoding="utf-8")

patches = [
    (
        """        b = re.sub(r"\\*\\*(.+?)\\*\\*", r"<strong>\\1</strong>", b)
        extra = ""
        if num == "8":
            pv = max(5, min(100, int(meta.get("pressure", 50))))
            extra = f'<motion class="mi-bar" title="Fan stress meter for {html.escape(fan_nick(team_name))} (higher = heavier)"><span style="width:{pv}%"></span></motion>'
        st.markdown(
            f"<motion class='mi-card {cls}'><motion class='mi-num'>SECTION {num}</motion>"
            f"<motion class='mi-title'>{safe_title}</motion><motion class='mi-body'>{b}</motion>{extra}</motion>",
            unsafe_allow_html=True,
        )""".replace("motion", "div"),
        """        b = re.sub(r"\\*\\*(.+?)\\*\\*", r"<strong>\\1</strong>", b)
        mom_pill = ""
        if kind == "momentum" and tone in ("up", "down", "flat"):
            lbl = {"up": "Swing up", "down": "Swing down", "flat": "Flat"}.get(tone, "")
            mom_pill = f'<span class="mi-mom-pill {tone}">{lbl}</span>'
        extra = ""
        if num == "8":
            pv = max(5, min(100, int(meta.get("pressure", 50))))
            extra = f'<motion class="mi-bar" title="Fan stress meter for {html.escape(fan_nick(team_name))} (higher = heavier)"><span style="width:{pv}%"></span></motion>'
        st.markdown(
            f"<motion class='mi-card {cls}'><motion class='mi-num'>SECTION {num}</motion>"
            f"<motion class='mi-title'>{safe_title}{mom_pill}</motion><motion class='mi-body'>{b}</motion>{extra}</motion>",
            unsafe_allow_html=True,
        )""".replace("motion", "motion"),
    ),
]
