"""
Asset Digital Thread Service
----------------------------
Central orchestration service that connects the entire machine lifecycle:
Asset -> Components -> Sensors -> Telemetry -> Features -> Predictions -> Anomalies -> RUL -> Drift Events -> Maintenance -> Parts -> Maintenance Outcome
"""

import time
import logging
import datetime
from typing import Dict, List, Any, Optional

from .config import config
from .database import db

logger = logging.getLogger("digital_thread_service")


class DigitalThreadService:
    """Production service managing the Asset Digital Thread lifecycle."""

    def __init__(self):
        self.config = config
        self.db = db
        
        # In-memory tracking of last logged state per asset to prevent event log flooding
        self.last_event_times: Dict[str, float] = {}
        self.last_anomaly_status: Dict[str, str] = {}
        self.last_rul_values: Dict[str, float] = {}
        self.last_drift_status: Dict[str, str] = {}
        self.last_telemetry_checkpoint: Dict[str, float] = {}

    def resolve_asset_id(self, plc_or_asset_id: str) -> str:
        """Translates PLC ID (e.g. PLC_01) to canonical Asset ID (e.g. COMP-001) or returns input."""
        if not plc_or_asset_id:
            return "COMP-001"
        cleaned = str(plc_or_asset_id).strip()
        if cleaned in self.config.PLC_TO_ASSET_MAP:
            return self.config.PLC_TO_ASSET_MAP[cleaned]
        return cleaned

    def resolve_plc_id(self, asset_or_plc_id: str) -> str:
        """Translates Asset ID (e.g. COMP-001) to PLC ID (e.g. PLC_01) or returns input."""
        if not asset_or_plc_id:
            return "PLC_01"
        cleaned = str(asset_or_plc_id).strip()
        if cleaned in self.config.ASSET_TO_PLC_MAP:
            return self.config.ASSET_TO_PLC_MAP[cleaned]
        return cleaned

    # -------------------------------------------------------------
    # TELEMETRY & ML EVENT INGESTION HOOKS
    # -------------------------------------------------------------

    def ingest_telemetry_event(self, record: Dict[str, Any]):
        """
        Ingests real-time telemetry record and ML results from the streaming pipeline.
        Records events when significant lifecycle milestones or state changes occur.
        """
        if not isinstance(record, dict):
            return

        plc_id = str(record.get("plc_id", "PLC_01"))
        asset_id = self.resolve_asset_id(plc_id)
        now_ts = time.time()
        ts_str = record.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        health = float(record.get("machine_health", record.get("Machine_Health", 100.0)))
        rul = int(record.get("predicted_rul_days", record.get("Predicted_RUL", 250)))
        status = str(record.get("machine_status", record.get("Machine_Status", "RUNNING")))
        anomaly_status = str(record.get("anomaly_status", record.get("Anomaly_Status", "Normal")))
        anomaly_score = float(record.get("Anomaly_Score", 0.0) or 0.0)

        # 1. Update Asset Health in Database
        self.db.update_asset_health(asset_id, health, rul, status)

        # 2. Anomaly State Change Event
        prev_anom = self.last_anomaly_status.get(asset_id, "Normal")
        if anomaly_status != prev_anom:
            self.last_anomaly_status[asset_id] = anomaly_status
            if anomaly_status != "Normal":
                vib = record.get("vibration", record.get("Vibration_X", 0.2))
                temp = record.get("temperature", record.get("Motor_Temp", 62.0))
                self.db.record_event(
                    asset_id=asset_id,
                    event_type="ANOMALY",
                    severity="WARNING" if "Warning" in anomaly_status else "CRITICAL",
                    source="Isolation Forest Model",
                    description=f"Operational Anomaly detected: {anomaly_status} (Score: {round(anomaly_score, 3)}, Vib: {vib} mm/s, Temp: {temp} °C)",
                    component_id=f"{asset_id}-BRG" if vib > 0.5 else f"{asset_id}-MOT",
                    sensor_id=f"SENS-{asset_id[-3:]}-T102" if vib > 0.5 else f"SENS-{asset_id[-3:]}-T101",
                    metric_value=round(anomaly_score, 3),
                    timestamp=ts_str,
                    metadata={"anomaly_score": anomaly_score, "temperature": temp, "vibration": vib}
                )

        # 3. Significant RUL Shift Event (shifts > 20 days)
        prev_rul = self.last_rul_values.get(asset_id, None)
        if prev_rul is not None and abs(rul - prev_rul) >= 25:
            self.last_rul_values[asset_id] = rul
            self.db.record_event(
                asset_id=asset_id,
                event_type="PREDICTION",
                severity="WARNING" if rul < 60 else "INFO",
                source="Random Forest RUL Regressor",
                description=f"RUL estimate updated: {rul} operating days remaining (Previous: {int(prev_rul)} days).",
                metric_value=float(rul),
                timestamp=ts_str,
                metadata={"predicted_rul": rul, "previous_rul": int(prev_rul), "model": record.get("model_used", "Random Forest Regressor")}
            )
        elif prev_rul is None:
            self.last_rul_values[asset_id] = rul

        # 4. Periodic Telemetry Checkpoint (every 60 seconds)
        last_ckpt = self.last_telemetry_checkpoint.get(asset_id, 0.0)
        if (now_ts - last_ckpt) >= 60.0:
            self.last_telemetry_checkpoint[asset_id] = now_ts
            temp = record.get("temperature", record.get("Motor_Temp", 62.0))
            vib = record.get("vibration", record.get("Vibration_X", 0.2))
            curr = record.get("motor_current", record.get("Motor_Current", 8.0))
            self.db.record_event(
                asset_id=asset_id,
                event_type="TELEMETRY",
                severity="INFO",
                source="MQTT SCADA Bridge",
                description=f"Telemetry Checkpoint: Temp={temp}°C, Vib={vib}mm/s, Curr={curr}A, Health={health}%",
                timestamp=ts_str,
                metadata={"temperature": temp, "vibration": vib, "motor_current": curr, "health": health, "rul": rul}
            )

    def ingest_drift_event(self, plc_id: str, drift_data: Dict[str, Any]):
        """
        Receives notification from Drift Monitoring subsystem and connects it to the Asset Digital Thread.
        """
        asset_id = self.resolve_asset_id(plc_id)
        now_str = drift_data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        overall_status = drift_data.get("overall_status", "NORMAL")

        prev_drift = self.last_drift_status.get(asset_id, "NORMAL")
        if overall_status != "HEALTHY" and (overall_status != prev_drift or (time.time() - self.last_event_times.get(f"{asset_id}_drift", 0.0)) > 300.0):
            self.last_drift_status[asset_id] = overall_status
            self.last_event_times[f"{asset_id}_drift"] = time.time()
            
            psi_score = drift_data.get("overall_drift_score", 0.0)
            reason = drift_data.get("reason", "Feature or prediction drift detected.")
            severity = "CRITICAL" if overall_status == "CRITICAL" else "WARNING"

            self.db.record_event(
                asset_id=asset_id,
                event_type="DRIFT",
                severity=severity,
                source="Drift & Reliability Engine",
                description=f"Data/Model Drift Detected ({overall_status}): {reason} (PSI: {round(psi_score, 3)})",
                metric_value=round(psi_score, 3),
                timestamp=now_str,
                metadata={
                    "run_id": drift_data.get("run_id"),
                    "psi_score": psi_score,
                    "drifted_features_count": drift_data.get("drifted_features_count", 0),
                    "recommendation": drift_data.get("recommendation")
                }
            )

    # -------------------------------------------------------------
    # ASSET HEALTH SNAPSHOT GENERATION
    # -------------------------------------------------------------

    def get_asset_health_snapshot(self, asset_id_or_plc: str,
                                  live_telemetry_dict: Dict[str, Any] = None,
                                  drift_service_ref: Any = None) -> Dict[str, Any]:
        """
        Synthesizes complete real-time health snapshot for the digital thread dashboard:
        - Asset details & components
        - Live sensor readings mapped to physical components
        - Isolation Forest anomaly analysis
        - Random Forest RUL estimation
        - Drift monitoring evaluation & PSI scores
        - Open maintenance items and last verified outcome
        """
        asset = self.db.get_asset_by_id(asset_id_or_plc)
        if not asset:
            # Fallback to COMP-001
            asset = self.db.get_asset_by_id("COMP-001")
            if not asset:
                raise ValueError(f"Asset '{asset_id_or_plc}' not found.")

        asset_id = asset["asset_id"]
        plc_id = asset["plc_id"]

        # 1. Overlay live telemetry values if available
        live_data = live_telemetry_dict or {}
        health = float(live_data.get("machine_health", asset.get("health", 100.0)))
        rul = int(live_data.get("predicted_rul_days", asset.get("rul_days", 250)))
        status = str(live_data.get("machine_status", asset.get("status", "RUNNING")))
        anomaly_status = str(live_data.get("anomaly_status", "Normal"))
        anomaly_score = float(live_data.get("Anomaly_Score", 0.0) or 0.0)

        # 2. Attach live readings to component sensors
        components = self.db.get_asset_components(asset_id)
        for comp in components:
            for sens in comp.get("sensors", []):
                tag = sens["tag_name"]
                if tag in live_data:
                    sens["live_value"] = float(live_data[tag])
                elif tag == "Motor_Temp" and "temperature" in live_data:
                    sens["live_value"] = float(live_data["temperature"])
                elif tag == "Vibration_X" and "vibration" in live_data:
                    sens["live_value"] = float(live_data["vibration"])
                elif tag == "Motor_Current" and "motor_current" in live_data:
                    sens["live_value"] = float(live_data["motor_current"])
                elif tag == "Pressure_Inlet" and "pressure" in live_data:
                    sens["live_value"] = float(live_data["pressure"])
                elif tag == "Noise" and "noise" in live_data:
                    sens["live_value"] = float(live_data["noise"])
                else:
                    sens["live_value"] = None

        # 3. Pull latest Drift evaluation if drift service provided
        drift_info = {
            "overall_status": "HEALTHY",
            "overall_drift_score": 0.02,
            "data_drift_status": "NORMAL",
            "prediction_drift_status": "NORMAL",
            "data_quality_status": "GOOD",
            "reason": "Feature distributions aligned with reference baseline."
        }
        if drift_service_ref:
            try:
                latest_eval = drift_service_ref.get_latest_evaluation(plc_id)
                if latest_eval:
                    drift_info = {
                        "overall_status": latest_eval.get("overall_status", "HEALTHY"),
                        "overall_drift_score": latest_eval.get("overall_drift_score", 0.0),
                        "data_drift_status": latest_eval.get("data_drift_status", "NORMAL"),
                        "prediction_drift_status": latest_eval.get("prediction_drift_status", "NORMAL"),
                        "data_quality_status": latest_eval.get("data_quality_status", "GOOD"),
                        "reason": latest_eval.get("reason", "Baseline aligned."),
                        "recommendation": latest_eval.get("recommendation", "Routine monitoring.")
                    }
            except Exception as e:
                logger.debug(f"Snapshot drift fetch: {e}")

        # 4. Fetch recent timeline events & maintenance
        timeline = self.db.get_asset_timeline(asset_id, limit=20)
        maintenance = self.db.get_asset_maintenance_history(asset_id)

        return {
            "asset_id": asset_id,
            "asset_name": asset["asset_name"],
            "asset_type": asset["asset_type"],
            "plc_id": plc_id,
            "location": asset["location"],
            "manufacturer": asset["manufacturer"],
            "model": asset["model"],
            "install_date": asset["install_date"],
            "status": status,
            "health": round(health, 1),
            "rul_days": rul,
            "last_maintenance_date": asset.get("last_maintenance_date"),
            "next_maintenance_date": asset.get("next_maintenance_date"),
            "components": components,
            "ai_health": {
                "health_status": "CRITICAL" if health < 60 else ("WARNING" if health < 80 else "HEALTHY"),
                "anomaly_status": anomaly_status,
                "anomaly_score": round(anomaly_score, 3),
                "predicted_rul": rul,
                "confidence_pct": float(live_data.get("prediction_confidence", 96.5)),
                "model_used": str(live_data.get("model_used", "Random Forest Regressor")),
                "drift": drift_info
            },
            "recent_events": timeline[:5],
            "maintenance_summary": {
                "total_records": len(maintenance),
                "latest_record": maintenance[0] if maintenance else None,
                "open_count": sum(1 for m in maintenance if m.get("status") in ["IN_PROGRESS", "SCHEDULED"])
            }
        }


digital_thread_service = DigitalThreadService()
