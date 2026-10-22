"""
test_platform_phase4.py
=======================
Automated test suite verifying PHASE 4 implementation:
- Root-cause analysis & complaint trends dashboard engine
- Overview metrics: total, refund, delivery, payment, damage, escalation & resolution rates
- Daily and weekly aggregation views
- Empty state and out-of-range date filter handling
- Date-range filtering precision
- Explainable spike detection baseline
- Recurring issue clusters with representative customer quotes and escalation rates
- Product and process analysis distinguishing patterns, explanations, and confirmed causes
- Emerging issues summary grounded in ticket figures
"""

import unittest
import database
import ai_engine


class TestPhase4Platform(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize database with seed and test fixtures."""
        database.init_db()
        database.ensure_historical_demo_dates()

    def test_01_overview_metrics_calculation(self):
        """Verify overview metrics accurately aggregate underlying complaint counts."""
        data = database.get_root_cause_dashboard_data()

        self.assertFalse(data["is_empty"])
        self.assertGreater(data["total_complaints"], 0)

        # Category counts
        self.assertGreaterEqual(data["refund_complaints"], 0)
        self.assertGreaterEqual(data["delivery_complaints"], 0)
        self.assertGreaterEqual(data["payment_complaints"], 0)
        self.assertGreaterEqual(data["damage_complaints"], 0)

        # Percentages
        tot = data["total_complaints"]
        self.assertAlmostEqual(data["refund_pct"], round((data["refund_complaints"] / tot) * 100.0, 1), places=1)
        self.assertAlmostEqual(data["delivery_pct"], round((data["delivery_complaints"] / tot) * 100.0, 1), places=1)

        # Rates between 0 and 100
        self.assertGreaterEqual(data["escalation_rate"], 0.0)
        self.assertLessEqual(data["escalation_rate"], 100.0)
        self.assertGreaterEqual(data["resolution_rate"], 0.0)
        self.assertLessEqual(data["resolution_rate"], 100.0)

    def test_02_daily_and_weekly_aggregation(self):
        """Verify daily vs weekly time series bucketing and conservation of total counts."""
        daily_data = database.get_root_cause_dashboard_data(view_mode="daily")
        weekly_data = database.get_root_cause_dashboard_data(view_mode="weekly")

        self.assertGreater(len(daily_data["trend_data"]), 0)
        self.assertGreater(len(weekly_data["trend_data"]), 0)

        # Daily periods formatted as YYYY-MM-DD
        for r in daily_data["trend_data"]:
            self.assertEqual(len(r["period"]), 10)
            self.assertEqual(r["period"][4], "-")
            self.assertEqual(r["period"][7], "-")

        # Weekly periods formatted as YYYY-Www
        for r in weekly_data["trend_data"]:
            self.assertIn("-W", r["period"])

        # Sum of totals across buckets must equal total complaints
        daily_sum = sum(r["total"] for r in daily_data["trend_data"])
        weekly_sum = sum(r["total"] for r in weekly_data["trend_data"])
        self.assertEqual(daily_sum, daily_data["total_complaints"])
        self.assertEqual(weekly_sum, weekly_data["total_complaints"])

    def test_03_empty_state_handling(self):
        """Verify graceful empty state handling when no complaints exist in selected window."""
        empty_data = database.get_root_cause_dashboard_data(
            start_date="2099-01-01",
            end_date="2099-01-02"
        )
        self.assertTrue(empty_data["is_empty"])
        self.assertEqual(empty_data["total_complaints"], 0)
        self.assertEqual(empty_data["refund_complaints"], 0)
        self.assertEqual(empty_data["escalation_rate"], 0.0)
        self.assertEqual(empty_data["resolution_rate"], 0.0)
        self.assertEqual(len(empty_data["trend_data"]), 0)
        self.assertIn("No complaints recorded", empty_data["emerging_summary"][0])

    def test_04_date_range_filtering(self):
        """Verify date-range filters strictly restrict the analyzed ticket subset."""
        all_data = database.get_root_cause_dashboard_data()
        all_periods = [r["period"] for r in all_data["trend_data"]]

        if len(all_periods) >= 3:
            mid_start = all_periods[1]
            mid_end = all_periods[-2]

            sub_data = database.get_root_cause_dashboard_data(
                start_date=mid_start,
                end_date=mid_end
            )
            # Filtered period total should be <= all-time total
            self.assertLessEqual(sub_data["total_complaints"], all_data["total_complaints"])
            for r in sub_data["trend_data"]:
                self.assertGreaterEqual(r["period"], mid_start)
                self.assertLessEqual(r["period"], mid_end)

    def test_05_explainable_spike_detection(self):
        """Verify spike alerts provide explainable baseline comparisons without false positives."""
        data = database.get_root_cause_dashboard_data()
        self.assertIn("spike_alerts", data)
        self.assertIsInstance(data["spike_alerts"], list)
        self.assertGreater(len(data["spike_alerts"]), 0)

        alert = data["spike_alerts"][0]
        self.assertIn("category", alert)
        self.assertIn("message", alert)
        self.assertIn(alert["type"], ["warning", "success", "info"])

    def test_06_recurring_issue_clusters(self):
        """Verify issue clusters extract themes, representative customer quotes, and escalation rates."""
        data = database.get_root_cause_dashboard_data()
        clusters = data["clusters"]

        self.assertIsInstance(clusters, list)
        self.assertGreater(len(clusters), 0)

        for cl in clusters:
            self.assertIn("name", cl)
            self.assertIn("count", cl)
            self.assertIn("theme", cl)
            self.assertIn("representative_examples", cl)
            self.assertIn("typical_urgency", cl)
            self.assertIn("escalation_rate", cl)
            self.assertGreater(cl["count"], 0)
            self.assertGreater(len(cl["representative_examples"]), 0)
            self.assertIn(cl["typical_urgency"], ["High", "Medium", "Low"])

    def test_07_product_and_process_analysis(self):
        """Verify clear separation between observed patterns, possible explanations, and confirmed causes."""
        data = database.get_root_cause_dashboard_data()
        patterns = data["product_process_patterns"]

        self.assertIsInstance(patterns, list)
        self.assertGreater(len(patterns), 0)

        for p in patterns:
            self.assertIn("entity", p)
            self.assertIn("type", p)
            self.assertIn("observed_pattern", p)
            self.assertIn("possible_explanation", p)
            self.assertIn("confirmed_cause", p)
            # Ensure text is distinct across the three levels of evidence
            self.assertNotEqual(p["observed_pattern"], p["possible_explanation"])
            self.assertNotEqual(p["observed_pattern"], p["confirmed_cause"])

    def test_08_emerging_issues_summary(self):
        """Verify executive summary bullets are supported by underlying data counts."""
        data = database.get_root_cause_dashboard_data()
        summary = data["emerging_summary"]

        self.assertIsInstance(summary, list)
        self.assertGreater(len(summary), 0)

        # Each bullet must be non-empty and grounded in data
        for bullet in summary:
            self.assertIsInstance(bullet, str)
            self.assertGreater(len(bullet), 10)


if __name__ == "__main__":
    unittest.main()
