"""Tests for NBA Applied Math context extractors."""

from __future__ import annotations

import unittest

from applied_math_context import build_nba_applied_math_context


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

    def test_stat_gap_context_merged(self) -> None:
        session = {
            "favorite_team": "New York Knicks",
            "_ami_stat_gap_context": {
                "player": "Jalen Brunson",
                "stat_gap": {
                    "player": "Jalen Brunson",
                    "comparison": "Allan Houston",
                    "stat": "playoff rebounds",
                    "gap": 12,
                },
                "games_remaining": 4,
                "rate_needed": "3.0 RPG",
            },
        }
        ctx = build_nba_applied_math_context("Legacy Tracker", session)
        self.assertEqual(ctx.get("player"), "Jalen Brunson")
        self.assertEqual(ctx.get("games_remaining"), 4)


if __name__ == "__main__":
    unittest.main()
