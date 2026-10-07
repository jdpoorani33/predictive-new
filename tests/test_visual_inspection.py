import unittest
import numpy as np
import os
import sys

# Ensure root workspace is in sys.path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from visual_inspection import (
    VisualConfig,
    YOLO11Detector,
    validate_gold_reference,
    ReferenceComparator,
    VisualHealthEngine,
    TemporalValidator,
    MultiModalFusionEngine
)
from visual_inspection.preprocessing import load_image, validate_image_quality, align_components
from visual_inspection.generate_sample_data import generate_industrial_component_image
from visual_inspection.service import visual_inspection_service

class TestVisualInspectionModule(unittest.TestCase):

    def setUp(self):
        self.healthy_img = generate_industrial_component_image("motor_belt", has_defect=False)
        self.crack_img = generate_industrial_component_image("motor_belt", has_defect=True, defect_type="crack")
        self.corrosion_img = generate_industrial_component_image("motor_belt", has_defect=True, defect_type="corrosion")

    def test_1_gold_reference_validation(self):
        res_valid = validate_gold_reference(self.healthy_img)
        self.assertTrue(res_valid["is_valid"])
        self.assertEqual(res_valid["status"], "VALID")

        # Test invalid zero/corrupt image
        res_invalid = validate_gold_reference(None)
        self.assertFalse(res_invalid["is_valid"])
        self.assertEqual(res_invalid["status"], "INVALID")

    def test_2_image_quality_check(self):
        q_good = validate_image_quality(self.healthy_img)
        self.assertTrue(q_good["is_valid"])
        self.assertIn(q_good["quality_status"], ["GOOD", "ACCEPTABLE"])

        # Test blurry image quality check
        import cv2
        blurry_img = cv2.GaussianBlur(self.healthy_img, (35, 35), 0)
        q_blur = validate_image_quality(blurry_img)
        self.assertFalse(q_blur["is_valid"])

    def test_3_component_alignment(self):
        aligned, success, ratio = align_components(self.healthy_img, self.healthy_img)
        self.assertEqual(aligned.shape, self.healthy_img.shape)

    def test_4_reference_comparator(self):
        comparator = ReferenceComparator()
        # Same healthy image comparison should yield high similarity
        comp_healthy = comparator.compare(self.healthy_img, self.healthy_img)
        self.assertGreaterEqual(comp_healthy["similarity_score"], 75.0)
        self.assertFalse(comp_healthy["has_significant_deviation"])

        # Defective crack image vs healthy reference should show lower similarity
        comp_defect = comparator.compare(self.healthy_img, self.crack_img)
        self.assertLess(comp_defect["similarity_score"], comp_healthy["similarity_score"])

    def test_5_visual_health_engine(self):
        engine = VisualHealthEngine()
        # Case 1: Healthy image & reference -> HEALTHY
        eval_healthy = engine.evaluate(self.healthy_img, self.healthy_img, machine_id="PLC_01")
        self.assertEqual(eval_healthy["reference_status"], "VALID")
        self.assertIn(eval_healthy["visual_status"], ["HEALTHY", "WARNING"])

        # Case 5: Invalid reference -> Handles gracefully without crashing
        eval_no_ref = engine.evaluate(self.healthy_img, None, machine_id="PLC_01")
        self.assertEqual(eval_no_ref["reference_status"], "INVALID")

    def test_6_sensor_reliability_fusion(self):
        fusion = MultiModalFusionEngine()
        # Test Case: Overheating temp sensor (95°C) with NO visual heat signs -> Flags sensor SUSPICIOUS
        sensor_telemetry = {
            "temperature": 95.0,
            "vibration": 0.2,
            "motor_current": 8.0,
            "pressure": 5.0,
            "noise": 42.0,
            "machine_health": 80.0
        }
        visual_result = {
            "visual_status": "HEALTHY",
            "visual_health_score": 95.0,
            "detections": [],
            "has_defects": False
        }
        res = fusion.fuse(sensor_telemetry, visual_result)
        self.assertIn("sensor_reliability", res)
        self.assertFalse(res["sensor_reliability"]["is_reliable"])
        self.assertTrue(len(res["sensor_reliability"]["suspicious_sensors"]) > 0)
        self.assertEqual(res["sensor_reliability"]["suspicious_sensors"][0]["sensor"], "Motor Temperature")

    def test_7_service_integration(self):
        res = visual_inspection_service.analyze("PLC_01")
        self.assertIn("visual_status", res)
        self.assertIn("visual_health_score", res)
        self.assertIn("sensor_reliability", res)
        self.assertIn("images", res)
        self.assertIsNotNone(res["images"]["current_annotated"])

if __name__ == "__main__":
    unittest.main()
