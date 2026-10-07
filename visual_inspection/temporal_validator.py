from typing import Dict, List, Any
from .config import VisualConfig

class TemporalValidator:
    """
    Temporal Validation Engine for Visual Health Inspection.
    Tracks detection trends over time to prevent false alarm spikes from single transient frames.
    """

    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        # Per PLC observation history: { "PLC_01": [ { "status": "HEALTHY", "score": 95, "defects": [] }, ... ] }
        self.history_by_plc: Dict[str, List[Dict[str, Any]]] = {}

    def update_and_validate(self, plc_id: str, current_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingests the latest visual evaluation for a given machine PLC and applies temporal consistency analysis.
        Returns updated result with temporal confidence adjustments.
        """
        if plc_id not in self.history_by_plc:
            self.history_by_plc[plc_id] = []

        plc_hist = self.history_by_plc[plc_id]
        plc_hist.append(current_result)
        if len(plc_hist) > self.window_size:
            plc_hist.pop(0)

        raw_status = current_result.get("visual_status", "HEALTHY")
        raw_score = current_result.get("visual_health_score", 100.0)

        # Count recent defect observations in history window
        warning_count = sum(1 for r in plc_hist if r.get("visual_status") in ["WARNING", "SUSPICIOUS"])
        critical_count = sum(1 for r in plc_hist if r.get("visual_status") == "CRITICAL")
        total_recent = len(plc_hist)

        temporal_status = raw_status
        temporal_reason = ""
        is_persistent = False

        if raw_status == "CRITICAL":
            if total_recent >= 2 and (critical_count >= 2 or (critical_count + warning_count) >= 2):
                is_persistent = True
                temporal_reason = "Defect is persistent across consecutive visual observations."
            elif total_recent == 1:
                is_persistent = True
                temporal_reason = "High-confidence critical visual defect observed."
            else:
                # First transient spike of a critical defect
                temporal_status = "WARNING"
                temporal_reason = "First observation of potential defect. Under temporal verification."

        elif raw_status in ["WARNING", "SUSPICIOUS"]:
            if (critical_count + warning_count) >= 3:
                temporal_status = "CRITICAL"
                temporal_reason = "Repeated visual warning detections upgraded to Critical status."
            else:
                temporal_reason = "Isolated visual anomaly observed."

        validated_result = dict(current_result)
        validated_result["temporal_status"] = temporal_status
        validated_result["is_persistent_defect"] = is_persistent
        validated_result["observation_window_count"] = total_recent
        if temporal_reason:
            validated_result["temporal_note"] = temporal_reason

        return validated_result
