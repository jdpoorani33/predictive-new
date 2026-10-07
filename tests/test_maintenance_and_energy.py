import sys
import os
import unittest
from fastapi.testclient import TestClient

# Add project base directory to path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from main import app, process_mqtt_telemetry, global_cost_config, sim_state
from model.maintenance_engine import get_maintenance_recommendation, DEFAULT_COST_CONFIG

class TestMaintenanceAndEnergyFeatures(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_maintenance_recommendation_calculation(self):
        # Test healthy state
        m_healthy = get_maintenance_recommendation(
            predicted_rul=200,
            machine_health=100.0,
            sensor_telemetry={"temperature": 62.0, "vibration": 0.20, "motor_current": 8.0, "pressure": 5.0, "noise": 42.0},
            plc_id="PLC_01"
        )
        self.assertEqual(m_healthy["main_issue"], "Normal Operation")
        self.assertEqual(m_healthy["priority_level"], "Low")
        self.assertEqual(m_healthy["energy_status"], "Normal")

        # Test bearing degradation / high vibration state (e.g. PLC-3)
        m_bearing = get_maintenance_recommendation(
            predicted_rul=28,
            machine_health=65.0,
            sensor_telemetry={"temperature": 70.0, "vibration": 0.45, "motor_current": 9.2, "pressure": 5.0, "noise": 45.0},
            plc_id="PLC_03"
        )
        self.assertIn("Bearing", m_bearing["main_issue"])
        self.assertIn("PLC_03", m_bearing["human_readable_alert"])
        self.assertGreater(m_bearing["preventive_cost"], 0)
        self.assertGreater(m_bearing["expected_failure_cost"], 0)
        self.assertGreater(m_bearing["energy_inefficiency_pct"], 0)
        self.assertTrue(len(m_bearing["why_recommendation"]) > 0)

    def test_api_endpoints(self):
        # 1. Status API
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        self.assertIn("status", res.json())

        # 2. PLCs list API
        res_plcs = self.client.get("/api/plcs")
        self.assertEqual(res_plcs.status_code, 200)
        plcs = res_plcs.json().get("plcs", [])
        self.assertTrue(len(plcs) >= 5)

        # 3. Maintenance Overview API
        res_maint = self.client.get("/api/maintenance/overview")
        self.assertEqual(res_maint.status_code, 200)
        data_maint = res_maint.json()
        self.assertIn("summary_cards", data_maint)
        self.assertIn("table_rows", data_maint)
        self.assertIn("cost_chart_data", data_maint)
        self.assertIn("energy_chart_data", data_maint)

        # 4. Energy API
        res_energy = self.client.get("/api/energy?plc_id=PLC_01")
        self.assertEqual(res_energy.status_code, 200)
        energy_json = res_energy.json()
        self.assertIn("baseline_energy_kwh", energy_json)
        self.assertIn("current_energy_kwh", energy_json)

        # 5. Cost Config GET and POST
        res_cfg_get = self.client.get("/api/cost-config")
        self.assertEqual(res_cfg_get.status_code, 200)
        
        res_cfg_post = self.client.post("/api/cost-config", json={"labour_cost": 4000.0})
        self.assertEqual(res_cfg_post.status_code, 200)
        self.assertEqual(res_cfg_post.json()["config"]["labour_cost"], 4000.0)

        # 6. Add New PLC API
        res_add = self.client.post("/api/plcs/add", json={"plc_id": "PLC_06", "name": "Turbine Motor Unit 6"})
        self.assertEqual(res_add.status_code, 200)
        self.assertEqual(res_add.json()["plc_id"], "PLC_06")

        # Verify PLC_06 appears in /api/plcs
        res_plcs_after = self.client.get("/api/plcs")
        plc_ids = [p["plc_id"] for p in res_plcs_after.json()["plcs"]]
        self.assertIn("PLC_06", plc_ids)

if __name__ == "__main__":
    unittest.main()
