"""Tests for holdings and theme inference."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PC_LIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PC_LIB))

from pc_lib.holdings_inference import infer_holdings_map, infer_holdings_row  # noqa: E402
from pc_lib.theme_inference import infer_theme_registry, infer_thesis_registry  # noqa: E402


FIXTURE_SYMBOLS = [
    "VGSH",
    "MSFT",
    "AMZN",
    "GDMN",
    "IAUM",
    "ARE",
    "SPCX",
    "CRDO",
    "LITE",
    "XYZQ",
]

FIXTURE_MV = {
    "VGSH": 133736.10,
    "MSFT": 87231.56,
    "AMZN": 74685.30,
    "GDMN": 59911.50,
    "IAUM": 51331.50,
    "ARE": 71563.50,
    "SPCX": 25994.00,
    "CRDO": 20727.20,
    "LITE": 8011.60,
    "XYZQ": 1000.00,
}


class HoldingsInferenceTests(unittest.TestCase):
    def test_vgsh_classified_as_fixed_income(self) -> None:
        row = infer_holdings_row("VGSH")
        self.assertEqual(row["GICSSector"], "Fixed Income")
        self.assertEqual(row["AssetSubclass"], "Treasury ETF")

    def test_msft_has_gics_sector(self) -> None:
        row = infer_holdings_row("MSFT")
        self.assertEqual(row["GICSSector"], "Information Technology")

    def test_unknown_symbol_low_confidence(self) -> None:
        row = infer_holdings_row("ZZZZ")
        self.assertEqual(row["MappingConfidence"], "low")
        self.assertEqual(row["GICSSector"], "")


class ThemeInferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.holdings = infer_holdings_map(FIXTURE_SYMBOLS)
        self.registry, self.theme_map, self.coverage, self.log = infer_theme_registry(
            self.holdings, symbol_mv=FIXTURE_MV
        )
        self.by_sym = {(r["Symbol"]): r["ThemeId"] for r in self.theme_map}

    def test_multiple_themes_not_dominated_by_other(self) -> None:
        theme_ids = {r["ThemeId"] for r in self.theme_map}
        self.assertGreaterEqual(len(theme_ids), 5)
        other_weight = sum(
            float(r["WeightPct"])
            for r in self.coverage
            if r["ThemeId"] in ("THEME_UNASSIGNED", "THEME_OTHER")
        )
        self.assertLess(other_weight, 40.0)

    def test_vgsh_defensive_fixed_income(self) -> None:
        self.assertEqual(self.by_sym["VGSH"], "THEME_DEFENSIVE_FIXED_INCOME")

    def test_precious_metals_cluster(self) -> None:
        self.assertEqual(self.by_sym["GDMN"], "THEME_PRECIOUS_METALS")
        self.assertEqual(self.by_sym["IAUM"], "THEME_PRECIOUS_METALS")

    def test_reits(self) -> None:
        self.assertEqual(self.by_sym["ARE"], "THEME_REITS")

    def test_tech_names(self) -> None:
        self.assertEqual(self.by_sym["MSFT"], "THEME_TECH_AI")
        self.assertEqual(self.by_sym["CRDO"], "THEME_TECH_AI")
        self.assertEqual(self.by_sym["LITE"], "THEME_TECH_AI")

    def test_tactical_spcx(self) -> None:
        self.assertEqual(self.by_sym["SPCX"], "THEME_TACTICAL")

    def test_knowledge_override(self) -> None:
        knowledge = [
            {
                "Symbol": "XYZQ",
                "ThemeId": "THEME_CUSTOM_TEST",
                "MappingConfidence": "high",
                "PrimaryFlag": "true",
                "Notes": "user defined",
            }
        ]
        _, theme_map, _, _ = infer_theme_registry(
            self.holdings, symbol_mv=FIXTURE_MV, knowledge_theme_map=knowledge
        )
        by_sym = {r["Symbol"]: r["ThemeId"] for r in theme_map}
        self.assertEqual(by_sym["XYZQ"], "THEME_CUSTOM_TEST")

    def test_clustered_thesis_registry(self) -> None:
        symbols = [r["Symbol"] for r in self.holdings]
        registry, assignments = infer_thesis_registry(
            symbols, self.theme_map, theme_coverage=self.coverage, clustered=True
        )
        self.assertGreaterEqual(len(registry), 4)
        thesis_ids = {r["ThesisId"] for r in registry}
        self.assertIn("THESIS_DEFENSIVE_FIXED_INCOME", thesis_ids)
        self.assertIn("THESIS_TECH_AI", thesis_ids)


if __name__ == "__main__":
    unittest.main()
