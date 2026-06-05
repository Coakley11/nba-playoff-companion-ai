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



# Stale names that must not appear on current playoff rotations (Trae / Sochan cleanup pattern).

FORBIDDEN_IN_CURRENT_ROTATION = {

    "Atlanta Hawks": ["Trae Young"],

    "New York Knicks": ["Precious Achiuwa"],

    "San Antonio Spurs": ["Jeremy Sochan"],

}





def fail(msg: str) -> None:

    FAILURES.append(msg)

    print(f"FAIL: {msg}")





def ok(msg: str) -> None:

    print(f"OK: {msg}")





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





def _norm(name: str) -> str:

    return re.sub(r"\s+", " ", str(name or "").strip()).lower()





def _load_finals_g1_score(src: str) -> str:

    m = re.search(r'^FINALS_GAME1_CANONICAL_SCORE\s*=\s*"([^"]+)"', src, re.M)

    return m.group(1) if m else ""





def main() -> int:

    src = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")

    curated = _load_dict("CURRENT_PLAYOFF_LINEUPS", src)

    outdated = _load_dict("OUTDATED_PLAYOFF_PLAYERS", src)

    profiles = _load_dict("TEAM_PROFILES", src)

    finals_g1 = _load_finals_g1_score(src)



    print("=== Finals Game 1 canonical score ===")

    if finals_g1 != "Knicks 105, Spurs 95":

        fail(f"FINALS_GAME1_CANONICAL_SCORE expected Knicks 105, Spurs 95, got {finals_g1!r}")

    else:

        ok(f"FINALS_GAME1_CANONICAL_SCORE = {finals_g1!r}")

    if "Knicks 118, Spurs 112" in src and "FINALS_GAME1_CANONICAL_SCORE" not in src.split("Knicks 118, Spurs 112")[0][-200:]:

        # Allow literal only inside validation error strings, not in demo backup

        if 'Score":"Knicks 118, Spurs 112"' in src or "Score': 'Knicks 118, Spurs 112" in src:

            fail("streamlit_app still embeds incorrect Finals G1 118-112 in demo data")



    print("\n=== Forbidden / outdated players (rotation audit) ===")

    for team, banned in FORBIDDEN_IN_CURRENT_ROTATION.items():

        prof = profiles.get(team) or {}

        board = curated.get(team) or {}

        outdated_keys = {_norm(n) for n in outdated.get(team, [])}

        for name in banned:

            n = _norm(name)

            if n not in outdated_keys:

                fail(f"{team}: {name} must be listed in OUTDATED_PLAYOFF_PLAYERS")

            for slot in LINEUP_SLOTS:

                if board.get(slot) and _norm(board[slot]) == n:

                    fail(f"{team}: outdated {name} still on curated {slot}")

            for bench_name in board.get("bench") or []:

                if _norm(bench_name) == n:

                    fail(f"{team}: outdated {name} still on curated bench")

            for starter in prof.get("starters") or []:

                if _norm(starter) == n:

                    fail(f"{team}: outdated {name} still in TEAM_PROFILES starters")

            for sub in prof.get("subs") or []:

                if _norm(sub) == n:

                    fail(f"{team}: outdated {name} still in TEAM_PROFILES subs")

        if banned:

            ok(f"{team}: blocked {banned} from current rotation")



    print("\n=== Finals teams (P3) — curated matches profile ===")

    for team in ACTIVE_FINALS:

        board = curated.get(team) or {}

        prof = profiles.get(team) or {}

        if not board:

            fail(f"{team}: missing CURRENT_PLAYOFF_LINEUPS")

            continue

        starters = prof.get("starters") or []

        for slot in LINEUP_SLOTS:

            if not board.get(slot):

                fail(f"{team}: missing slot {slot}")

        for i, slot in enumerate(LINEUP_SLOTS):

            curated_name = board.get(slot, "")

            if i < len(starters) and curated_name != starters[i]:

                fail(

                    f"{team} {slot}: curated {curated_name!r} != "

                    f"TEAM_PROFILES starter {starters[i]!r}"

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

        missing_subs = [

            s

            for s in subs

            if _norm(s) not in {_norm(b) for b in bench}

            and _norm(s) not in outdated_keys

        ]

        if missing_subs:

            fail(f"{team}: profile subs missing from curated bench: {missing_subs}")

        print(f"  OK {team}: starters={[board[s] for s in LINEUP_SLOTS]} bench={bench}")



    print("\n=== Spurs rotation spot-check ===")

    sas = curated.get("San Antonio Spurs") or {}

    if _norm(sas.get("PF", "")) != _norm("Harrison Barnes"):

        fail(f"Spurs PF must be Harrison Barnes, got {sas.get('PF')!r}")

    elif any(_norm(sas.get(s, "")) == _norm("Jeremy Sochan") for s in LINEUP_SLOTS):

        fail("Jeremy Sochan still listed in Spurs curated starters")

    else:

        ok("Spurs PF is Harrison Barnes; Jeremy Sochan not in curated rotation")



    print("\n=== OUTDATED keys ===")

    for team, names in sorted(outdated.items()):

        if names:

            print(f"  {team}: {names}")



    if FAILURES:

        print(f"\n{len(FAILURES)} failure(s)")

        return 1

    print("\nOK — lineups audit passed.")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

