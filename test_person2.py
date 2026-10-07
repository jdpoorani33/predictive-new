import urllib.request
import json
import unittest
import sys

BASE_URL = "http://127.0.0.1:8000/api"

class TestPerson2Requirements(unittest.TestCase):

    def test_01_plc_01_motor_temp(self):
        url = f"{BASE_URL}/actual-vs-predicted?plc_id=PLC_01&target=Motor_Temp"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.status, 200)
        data = json.loads(req.read())
        
        self.assertEqual(data["plc_id"], "PLC_01")
        self.assertIn("actual", data)
        self.assertIn("predicted", data)
        self.assertGreater(len(data["actual"]), 0, "Actual data should not be empty")
        self.assertGreater(len(data["predicted"]), 0, "Predicted data should not be empty")
        print("\n[TEST PASS] Test 1: PLC_01 + Motor_Temp telemetry & predictions verified.")

    def test_02_plc_03_vibration(self):
        url = f"{BASE_URL}/actual-vs-predicted?plc_id=PLC_03&target=Vibration_X"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.status, 200)
        data = json.loads(req.read())
        
        self.assertEqual(data["plc_id"], "PLC_03")
        self.assertIn("actual", data)
        self.assertIn("predicted", data)
        self.assertGreater(len(data["actual"]), 0, "PLC_03 Vibration actual data present")
        print("[TEST PASS] Test 2: PLC_03 + Vibration telemetry & predictions verified.")

    def test_03_add_plc_06(self):
        url = f"{BASE_URL}/plcs/add"
        payload = json.dumps({"plc_id": "PLC_06"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        res = urllib.request.urlopen(req)
        self.assertEqual(res.status, 200)
        data = json.loads(res.read())
        self.assertEqual(data["plc_id"], "PLC_06")

        # Verify PLC_06 is in /api/plcs list
        plcs_res = urllib.request.urlopen(f"{BASE_URL}/plcs")
        plcs_data = json.loads(plcs_res.read())
        plc_ids = [p["plc_id"] for p in plcs_data.get("plcs", [])]
        self.assertIn("PLC_06", plc_ids, "PLC_06 should now be in the discovered PLCs list")
        print("[TEST PASS] Test 3: Dynamically added PLC_06 verified in PLC list.")

    def test_04_plc_06_mqtt_recognition(self):
        url = f"{BASE_URL}/current?plc_id=PLC_06"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.status, 200)
        data = json.loads(req.read())
        self.assertEqual(data["plc_id"], "PLC_06")
        self.assertIn("temperature", data)
        self.assertIn("vibration", data)
        self.assertIn("motor_current", data)
        self.assertIn("pressure", data)
        print("[TEST PASS] Test 4: PLC_06 telemetry state & predictions recognized by system.")

    def test_05_real_vs_guessed_same_chart(self):
        url = f"{BASE_URL}/actual-vs-predicted?plc_id=PLC_06&target=Motor_Temp"
        req = urllib.request.urlopen(url)
        self.assertEqual(req.status, 200)
        data = json.loads(req.read())
        
        actual_vals = data.get("actual", [])
        predicted_vals = data.get("predicted", [])
        
        self.assertGreater(len(actual_vals), 0, "Real sensor values present")
        self.assertGreater(len(predicted_vals), 0, "Guessed/Predicted values present")
        self.assertEqual(len(actual_vals), len(predicted_vals), "Real and Guessed arrays aligned in length")
        print(f"[TEST PASS] Test 5: Real vs Guessed chart series verified (Real={len(actual_vals)}, Guessed={len(predicted_vals)}).")

    def test_06_verify_no_srm_text(self):
        status_url = f"{BASE_URL}/status"
        req = urllib.request.urlopen(status_url)
        data = json.loads(req.read())
        data_str = json.dumps(data)
        self.assertNotIn("SRM", data_str)
        self.assertNotIn("srm", data_str.lower())
        print("[TEST PASS] Test 6: No visible SRM text remains.")

if __name__ == "__main__":
    unittest.main()
