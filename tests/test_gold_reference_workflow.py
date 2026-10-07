import sys
import os
import cv2
import json
import base64
import unittest
import numpy as np
from fastapi.testclient import TestClient

# Add project base directory to path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from main import app
from visual_inspection.service import VisualInspectionService
from visual_inspection.generate_sample_data import generate_industrial_component_image

class TestGoldReferenceWorkflow(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.plc_id = "PLC_01"

    def image_to_base64(self, img_array):
        _, buffer = cv2.imencode('.jpg', img_array)
        b64_str = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"

    def test_full_gold_reference_workflow(self):
        # STEP 1: Register healthy image as Gold Reference
        healthy_ref = generate_industrial_component_image("motor_belt", has_defect=False)
        ref_b64 = self.image_to_base64(healthy_ref)
        
        reg_res = self.client.post("/api/visual-inspection/reference", json={
            "plc_id": self.plc_id,
            "image_base64": ref_b64
        })
        self.assertEqual(reg_res.status_code, 200)
        reg_json = reg_res.json()
        self.assertEqual(reg_json.get("status"), "success")
        self.assertEqual(reg_json.get("reference_status"), "VALID")
        self.assertTrue(reg_json.get("version", "").startswith("v"))

        # STEP 2 & STEP 3: Verify Gold Reference metadata exists
        meta_res = self.client.get(f"/api/visual-inspection/reference/{self.plc_id}")
        self.assertEqual(meta_res.status_code, 200)
        meta_json = meta_res.json()
        self.assertEqual(meta_json.get("reference_status"), "VALID")
        self.assertTrue(meta_json.get("is_valid"))
        self.assertIn("version", meta_json)

        # STEP 4: Upload new healthy image -> High similarity + HEALTHY
        healthy_curr = generate_industrial_component_image("motor_belt", has_defect=False, lighting_offset=1.5)
        curr_b64 = self.image_to_base64(healthy_curr)

        healthy_insp = self.client.post("/api/visual-inspection/analyze", json={
            "plc_id": self.plc_id,
            "image_base64": curr_b64
        })
        self.assertEqual(healthy_insp.status_code, 200)
        h_json = healthy_insp.json()
        self.assertIn(h_json.get("status"), ["HEALTHY", "WARNING"])
        self.assertGreaterEqual(h_json.get("visual_health_score", 0), 80.0)
        self.assertGreaterEqual(h_json.get("reference_similarity", 0), 85.0)

        # STEP 5: Upload defective image -> YOLO detects defect + lower score
        defect_img = generate_industrial_component_image("motor_belt", has_defect=True, defect_type="crack")
        defect_b64 = self.image_to_base64(defect_img)

        defect_insp = self.client.post("/api/visual-inspection/analyze", json={
            "plc_id": self.plc_id,
            "image_base64": defect_b64
        })
        self.assertEqual(defect_insp.status_code, 200)
        d_json = defect_insp.json()
        self.assertTrue(d_json.get("has_defects") or d_json.get("visual_status") in ["WARNING", "CRITICAL"])
        self.assertLess(d_json.get("visual_health_score", 100), 90.0)

        # STEP 6: Upload blurry/invalid image -> UNCERTAIN/POOR status
        blurry_img = cv2.GaussianBlur(healthy_ref, (45, 45), 0)
        blurry_b64 = self.image_to_base64(blurry_img)

        blurry_insp = self.client.post("/api/visual-inspection/analyze", json={
            "plc_id": self.plc_id,
            "image_base64": blurry_b64
        })
        self.assertEqual(blurry_insp.status_code, 200)
        b_json = blurry_insp.json()
        self.assertIn(b_json.get("status"), ["UNCERTAIN", "WARNING"])
        self.assertEqual(b_json.get("image_quality_status"), "POOR")

        # STEP 7: Verify Gold Reference was NOT overwritten during normal inspection
        final_meta = self.client.get(f"/api/visual-inspection/reference/{self.plc_id}")
        self.assertEqual(final_meta.json().get("version"), reg_json.get("version"))

if __name__ == "__main__":
    unittest.main()
