"""Regression tests for period-scoped symbol metrics and fill dedupe.

Guards the two defects from the symbol-trade-review feedback:
1. symbol P&L silently lifetime-scoped when a period was requested
2. duplicate fills (same fill, different Market quote snapshot) double-counted by FIFO
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PC_LIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PC_LIB))

from pc_lib.analytics import filled_orders, symbol_metrics  # noqa: E402


def _order(time: str, side: str, qty: str, price: str, market: str = "--") -> dict[str, str]:
    return {
        "Symbol": "TST",
        "Status": "Filled",
        "Side": side,
        "Fill": f"{qty} @ {price}",
        "FillQuantity": qty,
        "FillPrice": price,
        "Market": market,
        "Time": time,
        "Date": time[:10],
        "Description": f"{side} {qty} Shares @ {price} Limit to Open",
        "AccountId": "900001001",
    }


# Window 2026-06-12..2026-06-15: buy 100 @ 10, sell 100 @ 12 -> +200 realized.
# After the window: buy 100 @ 20, sell 100 @ 5 -> -1500, dragging lifetime negative.
FIXTURE = [
    _order("2026-06-12 10:00:00", "Buy", "100", "10.00"),
    _order("2026-06-13 10:00:00", "Sell", "100", "12.00"),
    _order("2026-06-20 10:00:00", "Buy", "100", "20.00"),
    _order("2026-06-21 10:00:00", "Sell", "100", "5.00"),
]

# The same in-window sell exported twice with a different Market quote snapshot,
# as produced by overlapping E*TRADE order downloads.
DUPLICATE_ROW = _order("2026-06-13 10:00:00", "Sell", "100", "12.00", market="11.95")


class SymbolMetricsPeriodScopeTest(unittest.TestCase):
    def test_period_fifo_differs_from_lifetime_and_matches_hand_computation(self):
        metrics = symbol_metrics(FIXTURE, "TST", "20260612", "20260615")
        self.assertEqual(metrics["realized_pnl_fifo_ex_fees_period"], 200.0)
        self.assertEqual(metrics["realized_pnl_fifo_ex_fees_lifetime"], -1300.0)
        self.assertNotEqual(
            metrics["realized_pnl_fifo_ex_fees_period"],
            metrics["realized_pnl_fifo_ex_fees_lifetime"],
        )
        self.assertEqual(metrics["shares_bought_period"], 100.0)
        self.assertEqual(metrics["ending_shares_period"], 0)
        self.assertEqual(metrics["order_records_period"], 2)
        self.assertEqual(metrics["TST_order_records"], 4)

    def test_no_unqualified_pnl_key(self):
        metrics = symbol_metrics(FIXTURE, "TST", "20260612", "20260615")
        self.assertNotIn("realized_pnl_fifo_ex_fees", metrics)

    def test_lifetime_only_when_no_period_given(self):
        metrics = symbol_metrics(FIXTURE, "TST")
        self.assertIn("realized_pnl_fifo_ex_fees_lifetime", metrics)
        self.assertNotIn("realized_pnl_fifo_ex_fees_period", metrics)


class FillDedupeTest(unittest.TestCase):
    def test_duplicate_fill_rows_collapse(self):
        rows = FIXTURE + [DUPLICATE_ROW]
        filled = filled_orders(rows, symbol="TST")
        self.assertEqual(len(filled), 4)

    def test_fifo_not_inflated_by_duplicate_fill(self):
        rows = FIXTURE + [DUPLICATE_ROW]
        metrics = symbol_metrics(rows, "TST", "20260612", "20260615")
        self.assertEqual(metrics["realized_pnl_fifo_ex_fees_period"], 200.0)
        self.assertEqual(metrics["shares_sold_period"], 100.0)


if __name__ == "__main__":
    unittest.main()
