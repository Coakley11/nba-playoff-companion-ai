"""Tests for NBA Applied Math context extractors."""

from __future__ import annotations

import unittest

from applied_math_context import (
    build_nba_applied_math_context,
    record_legacy_stat_gap_context,
    record_matchup_intelligence_context,
)


class TestNbaAppliedMathContext(unittest.TestCase):
    def test_probability_context_includes_team_and_opponent(self) -> None:
        session = {
            "favorite_team": "New York Knicks",
            "live_win_prob_display": 62,
            "playoff_team_state": {
                "current_opponent": "Boston Celtics",
                "series_win_probability": 71,
            },
        }
        ctx = build_nba_applied_math_context("Live Game Center", session)
        self.assertEqual(ctx["team"], "New York Knicks")
        self.assertEqual(ctx["opponent"], "Boston Celtics")
        self.assertIn("62", str(ctx.get("win_probability", "")))

    def test_legacy_stat_gap_context(self) -> None:
        session: dict = {}
        record_legacy_stat_gap_context(
            session,
            player="Jalen Brunson",
            team_name="New York Knicks",
            stat_label="Playoff rebounds",
            stat_key="reb",
            current_value=8,
            target_name="Allan Houston",
            target_value=20,
            gap=12,
            games_remaining=4,
            rate_needed="3.0 RPG",
        )
        ctx = build_nba_applied_math_context("Legacy Tracker", session)
        self.assertEqual(ctx["player"], "Jalen Brunson")
        gap = ctx.get("stat_gap")
        self.assertIsInstance(gap, dict)
        self.assertEqual(gap.get("gap"), 12)
        self.assertEqual(gap.get("comparison"), "Allan Houston")

    def test_matchup_context_contains_metrics(self) -> None:
        session: dict = {}
        record_matchup_intelligence_context(
            session,
            team_name="New York Knicks",
            opponent="Boston Celtics",
            meta={"tw": 2, "ow": 1, "pressure": 55, "games_n": 3},
            section_summaries=["Knicks control the glass"],
            injury_summary="Anunoby questionable",
            key_players=["Jalen Brunson", "Jayson Tatum"],
            series_probability="62%",
        )
        ctx = build_nba_applied_math_context("Matchup Intelligence", session)
        self.assertIn("Knicks control", str(ctx.get("matchup_advantages")))
        self.assertEqual(ctx.get("injury_summary"), "Anunoby questionable")
        self.assertEqual(ctx.get("series_record"), "2-1")


if __name__ == "__main__":
    unittest.main()
