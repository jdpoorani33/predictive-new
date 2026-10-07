import unittest
import os
import sys
import json
import math

# Ensure root workspace is in sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from fastapi.testclient import TestClient
from main import app

class TestAnalyticsAndMaintenanceGraphs(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_actual_vs_predicted_endpoint(self):
        res = self.client.get("/api/analytics/actual-vs-predicted")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("data", data)
        self.assertIn("metrics", data)

        rows = data["data"]
        self.assertGreater(len(rows), 0)

        # Verify pairwise matching & numeric integrity
        first_row = rows[0]
        self.assertIn("actual", first_row)
        self.assertIn("predicted", first_row)
        self.assertIn("index", first_row)
        self.assertTrue(isinstance(first_row["actual"], (int, float)))
        self.assertTrue(isinstance(first_row["predicted"], (int, float)))
        self.assertFalse(math.isnan(first_row["actual"]))
        self.assertFalse(math.isnan(first_row["predicted"]))

        # Verify metrics calculation
        metrics = data["metrics"]
        self.assertIn("mae", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("r2_score", metrics)
        self.assertGreater(metrics["mae"], 0)
        self.assertGreater(metrics["rmse"], 0)

    def test_02_maintenance_history_endpoint(self):
        res = self.client.get("/api/maintenance/history?plc_id=PLC_01")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["plc_id"], "PLC_01")
        self.assertIn("data", data)

        rows = data["data"]
        self.assertGreater(len(rows), 0)

        # Verify cost fields in maintenance history
        first_row = rows[0]
        self.assertIn("expected_breakdown_loss", first_row)
        self.assertIn("preventive_cost", first_row)
        self.assertIn("failure_probability", first_row)
        self.assertIn("machine_health", first_row)
        self.assertIn("predicted_rul_days", first_row)
        self.assertTrue(isinstance(first_row["expected_breakdown_loss"], (int, float)))
        self.assertTrue(isinstance(first_row["preventive_cost"], (int, float)))

    def test_03_existing_endpoints_unaffected(self):
        # Verify status endpoint still works
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)

        # Verify visual inspection endpoint still works
        res_vis = self.client.get("/api/visual-inspection/result/PLC_01")
        self.assertEqual(res_vis.status_code, 200)

        # Verify drift monitoring endpoint still works
        res_drift = self.client.get("/api/drift/summary?plc_id=PLC_01")
        self.assertEqual(res_drift.status_code, 200)

if __name__ == "__main__":
    unittest.main()
