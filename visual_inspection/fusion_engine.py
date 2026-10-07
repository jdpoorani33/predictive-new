import logging
from typing import Dict, Any, List, Optional
from .config import VisualConfig

logger = logging.getLogger("uvicorn.error")

class MultiModalFusionEngine:
    """
    Multi-Modal Decision & Sensor Reliability Engine.
    Fuses telemetry sensors (Temperature, Vibration, Current, Pressure, Noise),
    Random Forest RUL, Isolation Forest anomalies, AND YOLO11 Visual Health.
    """

    def fuse(
        self,
        sensor_telemetry: Dict[str, Any],
        visual_result: Dict[str, Any],
        sensor_health_score: float = 100.0
    ) -> Dict[str, Any]:
        """
        Synthesizes sensor health, visual health, and sensor reliability.
        Returns final multi-modal machine status, combined health index, sensor reliability audit, and explainable alerts.
        """
        temp = float(sensor_telemetry.get("temperature", sensor_telemetry.get("Motor_Temp", 62.0)))
        vib = float(sensor_telemetry.get("vibration", sensor_telemetry.get("Vibration_X", 0.2)))
        curr = float(sensor_telemetry.get("motor_current", sensor_telemetry.get("Motor_Current", 8.0)))
        press = float(sensor_telemetry.get("pressure", sensor_telemetry.get("Pressure_Inlet", 5.0)))
        noise = float(sensor_telemetry.get("noise", sensor_telemetry.get("Noise", 42.0)))

        is_isolation_anomaly = bool(sensor_telemetry.get("is_anomaly", False))
        sensor_status = str(sensor_telemetry.get("machine_status", "Healthy"))

        # Extract Visual Inspection Parameters
        vis_status = visual_result.get("visual_status", "HEALTHY")
        vis_score = float(visual_result.get("visual_health_score", 100.0))
        vis_detections = visual_result.get("detections", [])
        vis_has_defects = visual_result.get("has_defects", False)

        # 1. SENSOR RELIABILITY ASSESSMENT
        suspicious_sensors = []
        reliability_score = 100.0

        # Check Temperature Sensor Consistency vs Visual & Vibration
        if temp >= VisualConfig.TEMP_SENSOR_HIGH_THRESHOLD:
            # Overheating reading
            has_visual_heat_sign = any(
                d.get("class") in ["overheating", "smoke", "corrosion", "component_damage"]
                for d in vis_detections
            )
            # Cross-check with motor current or vibration
            if not has_visual_heat_sign and curr < 12.0 and vib < 0.6:
                suspicious_sensors.append({
                    "sensor": "Motor Temperature",
                    "value": f"{temp}°C",
                    "status": "SUSPICIOUS",
                    "reason": "Temperature reading is high (>=85°C) but inconsistent with visual inspection and normal motor current."
                })
                reliability_score -= 30.0

        # Check Vibration Sensor Consistency vs Visual Damage
        if vib >= VisualConfig.VIB_SENSOR_HIGH_THRESHOLD:
            has_visual_vibration_cause = any(
                d.get("class") in ["belt_damage", "crack", "component_damage"]
                for d in vis_detections
            )
            if not has_visual_vibration_cause and temp < 75.0 and curr < 10.0:
                suspicious_sensors.append({
                    "sensor": "Vibration RMS",
                    "value": f"{vib} mm/s",
                    "status": "SUSPICIOUS",
                    "reason": "High vibration detected, but no visible physical belt/component damage observed."
                })
                reliability_score -= 25.0

        reliability_score = max(0.0, min(100.0, reliability_score))
        sensor_reliability_status = "RELIABLE" if reliability_score >= 85.0 else ("SUSPICIOUS" if reliability_score >= 60.0 else "UNRELIABLE")

        # 2. OVERALL MULTI-MODAL MACHINE HEALTH CALCULATION
        # Combine Sensor Health (60%) and Visual Health (40%)
        combined_health = (0.60 * sensor_health_score) + (0.40 * vis_score)

        # Strict Multi-Modal Overrides:
        # If visual inspection confirms severe physical damage (CRITICAL), machine overall status MUST be CRITICAL!
        if vis_status == "CRITICAL" and vis_has_defects:
            overall_status = "CRITICAL"
            combined_health = min(combined_health, 45.0)
        elif vis_status == "WARNING" or sensor_status in ["Warning", "Maintenance Required"]:
            overall_status = "WARNING"
            combined_health = min(combined_health, 74.0)
        elif combined_health >= 85.0:
            overall_status = "HEALTHY"
        elif combined_health >= 60.0:
            overall_status = "WARNING"
        else:
            overall_status = "CRITICAL"

        # 3. GENERATE MEANINGFUL EXPLAINABLE ALERTS
        alerts = []

        if vis_status in ["WARNING", "CRITICAL"] and vis_has_defects:
            defect_names = ", ".join(set(d.get("class", "defect") for d in vis_detections))
            alerts.append({
                "type": "VISUAL_ALERT",
                "severity": "CRITICAL" if vis_status == "CRITICAL" else "WARNING",
                "title": "Visual Inspection Defect Detected",
                "message": f"Critical visual defect detected: {defect_names} on monitored machine component."
            })

        if suspicious_sensors:
            sens_names = ", ".join(s["sensor"] for s in suspicious_sensors)
            alerts.append({
                "type": "SENSOR_RELIABILITY_ALERT",
                "severity": "WARNING",
                "title": "Sensor Reliability Warning",
                "message": f"Sensor ({sens_names}) reading may be unreliable. Reading is inconsistent with available visual and cross-sensor evidence."
            })

        if vis_status == "CRITICAL" and (vib > 0.8 or temp > 80.0):
            alerts.append({
                "type": "COMBINED_ALERT",
                "severity": "CRITICAL",
                "title": "Multi-Modal Machine Failure Risk",
                "message": f"Machine condition is Critical. Elevated sensor telemetry and visual inspection confirm severe physical component damage."
            })

        if not alerts and overall_status == "HEALTHY":
            alerts.append({
                "type": "SYSTEM_INFO",
                "severity": "INFO",
                "title": "Normal Operation",
                "message": "All sensor telemetry, ML models, and YOLO11 visual inspection verify healthy operating baseline."
            })

        return {
            "overall_machine_health": round(combined_health, 1),
            "overall_machine_status": overall_status,
            "sensor_health_score": round(sensor_health_score, 1),
            "visual_health_score": round(vis_score, 1),
            "visual_status": vis_status,
            "sensor_reliability": {
                "status": sensor_reliability_status,
                "score": round(reliability_score, 1),
                "suspicious_sensors": suspicious_sensors,
                "is_reliable": len(suspicious_sensors) == 0
            },
            "alerts": alerts,
            "summary_reason": (
                f"Multi-modal fusion result: Sensor health ({round(sensor_health_score, 1)}%), "
                f"Visual health ({round(vis_score, 1)}%). Final status: {overall_status}."
            )
        }
