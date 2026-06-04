"""Matchup Lineups audit — curated boards vs TEAM_PROFILES (no Streamlit UI)."""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LINEUP_SLOTS = ("PG", "SG", "SF", "PF", "C")
ACTIVE_FINALS = ("New York Knicks", "San Antonio Spurs")
FAILURES: list[str] = []


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"FAIL: {msg}")


def _load_dict(name: str, src: str) -> dict:
    m = re.search(rf"^{name}\s*=\s*(\{{)", src, re.M)
    if not m:
        fail(f"{name} not found in streamlit_app.py")
        return {}
    start = m.start(1)
    depth = 0
    for i in range(start, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return ast.literal_eval(src[start : i + 1])
                except SyntaxError as exc:
                    fail(f"{name} parse error: {exc}")
                    return {}
    fail(f"{name} unterminated")
    return {}


def main() -> int:
    src = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    curated = _load_dict("CURRENT_PLAYOFF_LINEUPS", src)
    outdated = _load_dict("OUTDATED_PLAYOFF_PLAYERS", src)
    profiles = _load_dict("TEAM_PROFILES", src)

    print("=== Finals teams (P3) ===")
    for team in ACTIVE_FINALS:
        board = curated.get(team) or {}
        prof = profiles.get(team) or {}
        if not board:
            fail(f"{team}: missing CURRENT_PLAYOFF_LINEUPS")
            continue
        for slot in LINEUP_SLOTS:
            if not board.get(slot):
                fail(f"{team}: missing slot {slot}")
        starters = prof.get("starters") or []
        for i, slot in enumerate(LINEUP_SLOTS):
            if i < len(starters):
                curated_name = board.get(slot, "")
                prof_name = starters[i]
                if curated_name != prof_name:
                    print(
                        f"  WARN {team} {slot}: curated={curated_name!r} profile={prof_name!r}"
                    )
        outdated_keys = {_norm(n) for n in outdated.get(team, [])}
        for slot in LINEUP_SLOTS:
            if _norm(board[slot]) in outdated_keys:
                fail(f"{team}: starter {board[slot]} is OUTDATED")
        for name in board.get("bench") or []:
            if _norm(name) in outdated_keys:
                fail(f"{team}: bench {name} is OUTDATED")
        bench = board.get("bench") or []
        subs = prof.get("subs") or []
        missing_subs = [s for s in subs if _norm(s) not in {_norm(b) for b in bench} and _norm(s) not in outdated_keys]
        if missing_subs:
            print(f"  NOTE {team}: profile subs not on curated bench: {missing_subs}")
        print(f"  OK {team}: starters={ [board[s] for s in LINEUP_SLOTS] } bench={bench}")

    print("\n=== OUTDATED keys ===")
    for team, names in sorted(outdated.items()):
        if names:
            print(f"  {team}: {names}")

    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s)")
        return 1
    print("\nOK — lineups audit passed.")
    return 0


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", str(name or "").strip()).lower()


if __name__ == "__main__":
    raise SystemExit(main())
