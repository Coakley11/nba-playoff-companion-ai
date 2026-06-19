"""NBA sidebar insight copy — basketball-specific labels."""

from __future__ import annotations

import unittest

from suite_analytical_question import (
    NBA_INSIGHT_EXAMPLE_QUESTIONS,
    nba_insight_question_placeholder,
)


class TestNbaInsightCopy(unittest.TestCase):
    def test_placeholder_is_basketball_specific(self) -> None:
        ph = nba_insight_question_placeholder("Live Game Center")
        self.assertIn("Knicks", ph)
        self.assertNotIn("trend meaningful statistically", ph.lower())

    def test_examples_cover_matchup_and_playoff(self) -> None:
        joined = " ".join(NBA_INSIGHT_EXAMPLE_QUESTIONS).lower()
        self.assertIn("matchup", joined)
        self.assertIn("playoff", joined)


if __name__ == "__main__":
    unittest.main()
