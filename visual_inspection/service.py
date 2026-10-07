import os
import cv2
import json
import datetime
import hashlib
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from .config import VisualConfig
from .preprocessing import load_image, validate_image_quality
from .reference_validator import validate_gold_reference
from .detector import YOLO11Detector
from .reference_comparator import ReferenceComparator
from .visual_health import VisualHealthEngine
from .temporal_validator import TemporalValidator
from .fusion_engine import MultiModalFusionEngine
from .visualization import draw_detections, image_to_base64, create_side_by_side_comparison
from .generate_sample_data import generate_industrial_component_image

logger = logging.getLogger("uvicorn.error")

class VisualInspectionService:
    """
    Central Visual Inspection Service unifying Gold Reference Management,
    YOLO11 Detection, Visual Health Scoring, Temporal Validation, and Multi-Modal Fusion.
    """

    def __init__(self):
        self.health_engine = VisualHealthEngine()
        self.temporal_validator = TemporalValidator()
        self.fusion_engine = MultiModalFusionEngine()
        
        # Per PLC visual inspection cache: { "PLC_01": { ...latest result... } }
        self.latest_results: Dict[str, Dict[str, Any]] = {}
        self.history_records: Dict[str, List[Dict[str, Any]]] = {}

    def get_gold_reference_image(self, plc_id: str) -> Tuple[Optional[np.ndarray], str]:
        """Returns loaded Gold Reference image array and file path for a given PLC."""
        norm_plc = plc_id.upper() if plc_id else "PLC_01"
        plc_dir = os.path.join(VisualConfig.GOLD_REF_DIR, norm_plc)
        
        if os.path.exists(plc_dir):
            files = [f for f in os.listdir(plc_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            if files:
                ref_path = os.path.join(plc_dir, files[0])
                img = load_image(ref_path)
                return img, ref_path

        # Fallback: Check root sample reference
        sample_path = os.path.join(VisualConfig.SAMPLE_IMAGES_DIR, norm_plc, "healthy.jpg")
        if os.path.exists(sample_path):
            img = load_image(sample_path)
            return img, sample_path

        # Generate default healthy reference on-the-fly if missing
        os.makedirs(plc_dir, exist_ok=True)
        gen_path = os.path.join(plc_dir, "component_01.jpg")
        gen_img = generate_industrial_component_image("motor_belt", has_defect=False)
        cv2.imwrite(gen_path, gen_img)
        return gen_img, gen_path

    def get_gold_reference_metadata(self, plc_id: str, include_image: bool = False) -> Dict[str, Any]:
        """Returns verified Gold Reference metadata, version, quality metrics, and optional image b64."""
        norm_plc = plc_id.upper() if plc_id else "PLC_01"
        plc_dir = os.path.join(VisualConfig.GOLD_REF_DIR, norm_plc)
        meta_path = os.path.join(plc_dir, "metadata.json")
        
        img, img_path = self.get_gold_reference_image(norm_plc)
        
        meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
            except Exception:
                meta = {}

        val_res = validate_gold_reference(img) if img is not None else {"is_valid": False, "status": "INVALID"}
        
        updated_at = meta.get("updated_at") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        version = meta.get("version") or "v1"
        image_hash = meta.get("image_hash") or (hashlib.md5(img.tobytes()).hexdigest()[:10] if img is not None else "unknown")
        
        result = {
            "plc_id": norm_plc,
            "reference_status": "VALID" if val_res.get("is_valid", True) else "INVALID",
            "is_valid": bool(val_res.get("is_valid", True)),
            "version": version,
            "updated_at": updated_at,
            "image_hash": image_hash,
            "resolution": val_res.get("resolution", f"{img.shape[1]}x{img.shape[0]}" if img is not None else "N/A"),
            "quality_score": val_res.get("quality_score", 95.0),
            "reasons": val_res.get("reasons", []),
            "path": img_path
        }

        # Save metadata if missing
        if not os.path.exists(meta_path) and img is not None:
            os.makedirs(plc_dir, exist_ok=True)
            try:
                with open(meta_path, "w") as f:
                    json.dump(result, f, indent=2)
            except Exception:
                pass

        if include_image and img is not None:
            annotated = draw_detections(img, [], title=f"GOLD REFERENCE - {norm_plc} ({version})")
            result["image_base64"] = image_to_base64(annotated)

        return result

    def set_gold_reference_image(self, plc_id: str, image_input: Any) -> Dict[str, Any]:
        """Uploads and validates a new Gold Reference baseline image for a machine PLC."""
        norm_plc = plc_id.upper() if plc_id else "PLC_01"
        img = load_image(image_input)
        
        if img is None:
            return {
                "status": "error",
                "message": "Invalid or unreadable image provided for Gold Reference."
            }

        val_res = validate_gold_reference(img)
        if not val_res["is_valid"]:
            return {
                "status": "error",
                "message": f"Gold Reference rejected: {', '.join(val_res['reasons'])}",
                "reference_status": "INVALID",
                "details": val_res
            }

        plc_dir = os.path.join(VisualConfig.GOLD_REF_DIR, norm_plc)
        os.makedirs(plc_dir, exist_ok=True)
        save_path = os.path.join(plc_dir, "component_01.jpg")
        meta_path = os.path.join(plc_dir, "metadata.json")

        cur_version_num = 1
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    old_meta = json.load(f)
                    old_v = old_meta.get("version", "v1")
                    if old_v.startswith("v") and old_v[1:].isdigit():
                        cur_version_num = int(old_v[1:]) + 1
            except Exception:
                pass

        version_str = f"v{cur_version_num}"
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        img_hash = hashlib.md5(img.tobytes()).hexdigest()[:10]

        # Save image file permanently
        cv2.imwrite(save_path, img)

        # Save metadata
        meta_data = {
            "plc_id": norm_plc,
            "reference_status": "VALID",
            "is_valid": True,
            "version": version_str,
            "updated_at": timestamp_str,
            "image_hash": img_hash,
            "resolution": val_res.get("resolution", f"{img.shape[1]}x{img.shape[0]}"),
            "quality_score": val_res.get("quality_score", 100.0),
            "reasons": [],
            "path": save_path
        }

        try:
            with open(meta_path, "w") as f:
                json.dump(meta_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save Gold Reference metadata JSON: {e}")

        logger.info(f"Updated Gold Reference for {norm_plc} ({version_str}) at {save_path}")

        # Clear cached result so fresh comparison against new reference occurs
        if norm_plc in self.latest_results:
            del self.latest_results[norm_plc]

        return {
            "status": "success",
            "message": f"Gold Reference updated ({version_str}) and verified valid for {norm_plc}.",
            "plc_id": norm_plc,
            "reference_status": "VALID",
            "version": version_str,
            "updated_at": timestamp_str,
            "image_hash": img_hash,
            "resolution": val_res.get("resolution"),
            "quality_score": val_res.get("quality_score")
        }

    def analyze(
        self,
        plc_id: str,
        current_image_input: Optional[Any] = None,
        sensor_telemetry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs complete visual inspection against stored backend Gold Reference for a machine PLC.
        """
        norm_plc = plc_id.upper() if plc_id else "PLC_01"

        # Load Gold Reference & Metadata
        gold_img, gold_path = self.get_gold_reference_image(norm_plc)
        ref_meta = self.get_gold_reference_metadata(norm_plc)

        # Load Current Image
        if current_image_input is not None:
            curr_img = load_image(current_image_input)
        else:
            sample_def = os.path.join(VisualConfig.SAMPLE_IMAGES_DIR, norm_plc, "defective.jpg")
            sample_h = os.path.join(VisualConfig.SAMPLE_IMAGES_DIR, norm_plc, "healthy.jpg")
            target = sample_def if os.path.exists(sample_def) else sample_h
            curr_img = load_image(target) if os.path.exists(target) else gold_img

        if curr_img is None:
            curr_img = gold_img

        # 1. Run Visual Health Engine evaluation against backend Gold Reference
        health_eval = self.health_engine.evaluate(
            current_input=curr_img,
            gold_reference_input=gold_img,
            machine_id=norm_plc
        )

        # 2. Run Temporal Validation
        temp_eval = self.temporal_validator.update_and_validate(norm_plc, health_eval)

        # 3. Run Multi-Modal Fusion & Sensor Reliability Check
        sens_dict = sensor_telemetry or {
            "temperature": 64.0,
            "vibration": 0.22,
            "motor_current": 8.1,
            "pressure": 5.0,
            "noise": 42.0,
            "machine_health": 95.0,
            "machine_status": "Healthy"
        }
        sensor_health_score = float(sens_dict.get("machine_health", 95.0))
        fusion_res = self.fusion_engine.fuse(
            sensor_telemetry=sens_dict,
            visual_result=temp_eval,
            sensor_health_score=sensor_health_score
        )

        # 4. Generate Visual Overlay Images
        detections = temp_eval.get("detections", [])
        annotated_curr = draw_detections(curr_img, detections, title=f"INSPECTED IMAGE - {norm_plc}")
        curr_b64 = image_to_base64(annotated_curr)

        # Build concise maintenance recommendation
        vis_status = temp_eval.get("temporal_status", temp_eval.get("visual_status"))
        max_severity = temp_eval.get("max_severity", "none")
        if vis_status == "HEALTHY":
            recommendation = "Component is visually healthy and aligns with verified Gold Reference."
        elif vis_status == "CRITICAL":
            recommendation = f"Critical physical defect ({max_severity}) detected. Immediate visual and mechanical servicing recommended."
        elif vis_status == "WARNING":
            recommendation = "Minor component defect or visual difference detected. Schedule visual inspection within 7–14 days."
        else:
            recommendation = "Inspection uncertain due to image quality or invalid reference. Re-inspect with a clear image."

        final_result = {
            "plc_id": norm_plc,
            "machine_id": norm_plc,
            "visual_status": vis_status,
            "status": vis_status,
            "visual_health_score": temp_eval.get("visual_health_score"),
            "reference_status": ref_meta.get("reference_status", "VALID"),
            "reference_version": ref_meta.get("version", "v1"),
            "reference_updated_at": ref_meta.get("updated_at"),
            "reference_similarity": temp_eval.get("reference_similarity"),
            "image_quality_score": temp_eval.get("image_quality_score"),
            "image_quality_status": temp_eval.get("image_quality_status"),
            "detections": detections,
            "detections_count": temp_eval.get("detections_count", 0),
            "has_defects": temp_eval.get("has_defects", False),
            "highest_confidence": temp_eval.get("highest_confidence", 0.0),
            "max_severity": max_severity,
            "is_persistent_defect": temp_eval.get("is_persistent_defect", False),
            "recommendation": recommendation,
            "sensor_reliability": fusion_res.get("sensor_reliability", {}),
            "overall_machine_health": fusion_res.get("overall_machine_health"),
            "overall_machine_status": fusion_res.get("overall_machine_status"),
            "alerts": fusion_res.get("alerts", []),
            "evidence": temp_eval.get("evidence", []),
            "reason": temp_eval.get("reason"),
            "summary_reason": fusion_res.get("summary_reason"),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "images": {
                "current_annotated": curr_b64
            }
        }

        # Cache result
        self.latest_results[norm_plc] = final_result
        if norm_plc not in self.history_records:
            self.history_records[norm_plc] = []

        history_item = dict(final_result)
        history_item["images"] = None
        self.history_records[norm_plc].append(history_item)
        if len(self.history_records[norm_plc]) > 50:
            self.history_records[norm_plc].pop(0)

        return final_result

    def get_latest_result(self, plc_id: str) -> Dict[str, Any]:
        """Returns the cached latest result or runs fresh analysis."""
        norm_plc = plc_id.upper() if plc_id else "PLC_01"
        if norm_plc in self.latest_results:
            return self.latest_results[norm_plc]
        return self.analyze(norm_plc)

    def get_history(self, plc_id: str, limit: int = 30) -> Dict[str, Any]:
        """Returns visual inspection timeline for a given PLC."""
        norm_plc = plc_id.upper() if plc_id else "PLC_01"
        hist = self.history_records.get(norm_plc, [])
        return {
            "plc_id": norm_plc,
            "total_records": len(hist),
            "history": hist[-limit:]
        }

    def simulate_defect_scenario(
        self,
        plc_id: str = "PLC_01",
        mode: str = "crack",
        sensor_telemetry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Interactive demonstration sandbox endpoint for triggering visual defect scenarios.
        Note: NEVER overwrites the real stored Gold Reference in backend.
        """
        norm_plc = plc_id.upper() if plc_id else "PLC_01"

        if mode == "invalid_reference":
            dummy_curr = generate_industrial_component_image("motor_belt", has_defect=True, defect_type="crack")
            eval_res = self.health_engine.evaluate(current_input=dummy_curr, gold_reference_input=None, machine_id=norm_plc)
            eval_res["reference_status"] = "INVALID"
            return eval_res

        elif mode == "poor_quality":
            healthy_img = generate_industrial_component_image("motor_belt", has_defect=False)
            blurry_img = cv2.GaussianBlur(healthy_img, (35, 35), 0)
            return self.analyze(norm_plc, current_image_input=blurry_img, sensor_telemetry=sensor_telemetry)

        elif mode == "healthy":
            healthy_img = generate_industrial_component_image("motor_belt", has_defect=False, lighting_offset=2.0)
            return self.analyze(norm_plc, current_image_input=healthy_img, sensor_telemetry=sensor_telemetry)

        else:
            defect_img = generate_industrial_component_image("motor_belt", has_defect=True, defect_type=mode)
            return self.analyze(norm_plc, current_image_input=defect_img, sensor_telemetry=sensor_telemetry)

visual_inspection_service = VisualInspectionService()

