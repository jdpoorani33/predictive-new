import unittest
import os
import sys
import json

# Ensure root workspace is in sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from fastapi.testclient import TestClient
from main import app

class TestVisualInspectionAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_get_status_preservation(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("Random Forest Regressor", data["available_models"])

    def test_02_get_visual_result(self):
        res = self.client.get("/api/visual-inspection/result/PLC_01")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("visual_status", data)
        self.assertIn("visual_health_score", data)
        self.assertIn("reference_similarity", data)
        self.assertIn("sensor_reliability", data)
        self.assertIn("images", data)

    def test_03_get_visual_reference(self):
        res = self.client.get("/api/visual-inspection/reference/PLC_01")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["status"], "VALID")

    def test_04_get_visual_history(self):
        res = self.client.get("/api/visual-inspection/history/PLC_01")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("history", data)

    def test_05_simulate_defect_scenario(self):
        # Test Crack Defect mode
        res_crack = self.client.post(
            "/api/visual-inspection/simulate-defect",
            json={"plc_id": "PLC_01", "mode": "crack"}
        )
        self.assertEqual(res_crack.status_code, 200)
        data_crack = res_crack.json()
        self.assertIn(data_crack["visual_status"], ["WARNING", "CRITICAL"])
        self.assertTrue(data_crack["has_defects"])

        # Test Invalid Reference mode
        res_invalid = self.client.post(
            "/api/visual-inspection/simulate-defect",
            json={"plc_id": "PLC_01", "mode": "invalid_reference"}
        )
        self.assertEqual(res_invalid.status_code, 200)
        data_invalid = res_invalid.json()
        self.assertEqual(data_invalid["reference_status"], "INVALID")

    def test_06_post_visual_analyze(self):
        res = self.client.post(
            "/api/visual-inspection/analyze",
            json={"plc_id": "PLC_01"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("visual_health_score", data)

if __name__ == "__main__":
    unittest.main()
