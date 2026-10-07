import logging
from typing import Dict, Any, List, Optional
from .config import VisualConfig
from .reference_validator import validate_gold_reference
from .preprocessing import validate_image_quality, load_image
from .detector import YOLO11Detector
from .reference_comparator import ReferenceComparator

logger = logging.getLogger("uvicorn.error")

class VisualHealthEngine:
    """
    Visual Health Scoring & Decision Logic Layer.
    Synthesizes Gold Reference status, image quality, YOLO11 detections,
    and multi-metric similarity scores into a trustworthy, explainable visual health decision.
    """

    def __init__(self, detector: Optional[YOLO11Detector] = None):
        self.detector = detector or YOLO11Detector()
        self.comparator = ReferenceComparator()

    def evaluate(
        self,
        current_input: Any,
        gold_reference_input: Optional[Any] = None,
        machine_id: str = "PLC_01"
    ) -> Dict[str, Any]:
        """
        Runs the complete visual inspection workflow:
        1. Current image quality evaluation
        2. Gold Reference validation
        3. YOLO11 object defect detection
        4. Reference comparison (SSIM, ORB, Edges, Heatmap)
        5. Visual Health score calculation & decision logic (Cases 1 - 5)
        """
        curr_img = load_image(current_input)

        # 1. Current Image Quality Check
        quality_res = validate_image_quality(curr_img)
        if not quality_res["is_valid"] or quality_res["quality_status"] == "POOR":
            return {
                "machine_id": machine_id,
                "visual_status": "UNCERTAIN",
                "visual_health_score": 50.0,
                "reference_status": "NOT_EVALUATED",
                "reference_similarity": 0.0,
                "image_quality_score": quality_res.get("quality_score", 0.0),
                "image_quality_status": quality_res.get("quality_status", "POOR"),
                "detections": [],
                "evidence": quality_res.get("reasons", ["Poor image quality"]),
                "reason": "Inspection Uncertain: Image quality is insufficient for reliable defect detection."
            }

        # 2. Gold Reference Validation
        ref_res = validate_gold_reference(gold_reference_input)
        ref_is_valid = ref_res["is_valid"]
        ref_status = ref_res["status"]  # "VALID" or "INVALID"

        # 3. YOLO11 Inference
        yolo_res = self.detector.detect(curr_img)
        detections = yolo_res.get("detections", [])
        has_defects = yolo_res.get("has_defects", False)
        highest_conf = yolo_res.get("highest_confidence", 0.0)
        max_severity = yolo_res.get("max_severity", "none")

        # 4. Gold Reference Comparison (if reference is valid)
        comp_res = {}
        if ref_is_valid:
            comp_res = self.comparator.compare(gold_reference_input, curr_img)
            similarity = comp_res.get("similarity_score", 100.0)
        else:
            similarity = 100.0 if not has_defects else 50.0

        # 5. Visual Health Scoring & Case Decision Logic
        evidence = []
        visual_status = "HEALTHY"
        visual_score = 100.0

        if not ref_is_valid:
            evidence.append("Gold Reference image is invalid or missing.")

        # Aggregate Defect Area and Confidence
        total_defect_area_pct = sum(d.get("area_percentage", 0.0) for d in detections)

        # Deduct score for detected YOLO defects
        defect_deduction = 0.0
        for d in detections:
            conf = d.get("confidence", 0.0)
            area = d.get("area_percentage", 0.0)
            c_name = d.get("class", "defect")
            weight = VisualConfig.CLASS_SEVERITY_WEIGHTS.get(c_name, 2.0)

            ded = (conf * 40.0) + (area * 3.0 * weight)
            defect_deduction += ded
            evidence.append(f"{c_name.capitalize()} detected (confidence {int(conf*100)}%, area {area}%).")

        # Deduct score for Gold Reference deviation
        ref_deduction = 0.0
        if ref_is_valid:
            ref_dev = max(0.0, 100.0 - similarity)
            ref_deduction = ref_dev * 1.0
            if similarity < VisualConfig.SIMILARITY_HEALTHY:
                evidence.append(f"Significant visual deviation from healthy reference (similarity {similarity}%).")
            else:
                evidence.append(f"Visual structure aligns well with healthy reference (similarity {similarity}%).")

        raw_score = 100.0 - (defect_deduction + ref_deduction)
        visual_score = max(0.0, min(100.0, round(raw_score, 1)))

        # DECISION CASES (Cases 1 - 5)

        # CASE 5: Invalid reference or poor image quality
        if not ref_is_valid and has_defects and highest_conf < VisualConfig.HIGH_CONF_THRESHOLD:
            visual_status = "UNCERTAIN"
            visual_score = 50.0
            reason_str = "Inspection Uncertain: Reference image invalid and defect detection confidence is low."

        # CASE 1: No defect detected & High Similarity
        elif not has_defects and similarity >= VisualConfig.SIMILARITY_HEALTHY:
            visual_status = "HEALTHY"
            reason_str = "Component is visually healthy and aligns with verified Gold Reference."

        # CASE 2: High Confidence Defect & Structural Difference (CRITICAL)
        elif (has_defects and highest_conf >= VisualConfig.HIGH_CONF_THRESHOLD and similarity < VisualConfig.SIMILARITY_WARNING) or visual_score < 45.0:
            visual_status = "CRITICAL"
            reason_str = f"Critical visual defect confirmed! High-confidence defect detected with major structural deviation from reference."

        # CASE 3: Low/Moderate Confidence Defect or Minor Reference Difference (SUSPICIOUS / WARNING)
        elif (has_defects and highest_conf < VisualConfig.HIGH_CONF_THRESHOLD) or (similarity < VisualConfig.SIMILARITY_HEALTHY and similarity >= VisualConfig.SIMILARITY_WARNING):
            visual_status = "WARNING"
            reason_str = f"Visual Warning: Minor component anomaly or moderate difference from healthy reference."

        # CASE 4: Calibrated Defect Severity
        elif has_defects and max_severity in ["high", "critical"]:
            visual_status = "CRITICAL" if visual_score < 60.0 else "WARNING"
            reason_str = f"Visual defect ({max_severity} severity) detected on machine component."

        else:
            if visual_score >= 85.0:
                visual_status = "HEALTHY"
            elif visual_score >= 65.0:
                visual_status = "WARNING"
            else:
                visual_status = "CRITICAL"
            reason_str = f"Visual health score evaluated at {visual_score}/100."

        return {
            "machine_id": machine_id,
            "visual_status": visual_status,
            "visual_health_score": visual_score,
            "reference_status": ref_status,
            "reference_similarity": comp_res.get("similarity_score", 100.0) if ref_is_valid else None,
            "image_quality_score": quality_res.get("quality_score", 100.0),
            "image_quality_status": quality_res.get("quality_status", "GOOD"),
            "detections": detections,
            "detections_count": len(detections),
            "has_defects": has_defects,
            "highest_confidence": round(highest_conf, 3),
            "max_severity": max_severity,
            "evidence": evidence,
            "reason": reason_str,
            "comparison_details": {
                "ssim_score": comp_res.get("ssim_score"),
                "feature_match_score": comp_res.get("feature_match_score"),
                "edge_similarity_score": comp_res.get("edge_similarity_score"),
                "histogram_similarity": comp_res.get("histogram_similarity")
            } if ref_is_valid else {}
        }
