import sys
import os
import time
import json
import asyncio
import logging
import datetime
import threading
import paho.mqtt.client as mqtt
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

# Ensure project modules are discoverable
base_dir = os.path.dirname(os.path.abspath(__file__))
for folder in ['simulator', 'preprocessing', 'model', 'utils']:
    folder_path = os.path.join(base_dir, folder)
    if os.path.exists(folder_path) and folder_path not in sys.path:
        sys.path.append(folder_path)
if base_dir not in sys.path:
    sys.path.append(base_dir)

from simulator import RealTimeMachineSimulator
from predict import PredictiveMaintenanceModel, get_future_trend, filter_displayed_rul
from maintenance_engine import get_maintenance_recommendation
from preprocessing import load_data, preprocess_data
from utils import get_status_color

# OWASP Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*;"
        )
        return response

model_service = PredictiveMaintenanceModel()
sim_engine = RealTimeMachineSimulator(max_lifespan_days=250, degradation_factor=1.8, degradation_start_day=100)

df_eval = load_data()
df_eval.ffill(inplace=True)

class SimulationState:
    def __init__(self):
        self.auto_play = False
        self.simulation_speed = 1.0
        self.history_records = []
        self.plc_records = {}  # {plc_id: latest_record_dict}
        self.prev_displayed_rul = {} # {plc_id: val}
        self.prev_status_level = {} # {plc_id: level}

    def reset(self):
        self.auto_play = False
        self.history_records = []
        self.plc_records = {}
        self.prev_displayed_rul = {}
        self.prev_status_level = {}

    def get_plc_status(self, plc_id=1):
        if plc_id in self.plc_records:
            return self.plc_records[plc_id]
        # Generate default record if not yet received
        return {
            "plc_id": plc_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": 62.4,
            "vibration": 0.21,
            "motor_current": 8.1,
            "pressure": 5.0,
            "noise": 42.1,
            "machine_health": 100.0,
            "machine_status": "Healthy",
            "machine_condition": "Healthy",
            "predicted_rul_days": 250,
            "actual_rul_days": 250,
            "failure_risk_pct": 0.0,
            "anomaly_status": "Normal",
            "prediction_confidence": 98.5,
            "model_used": "Random Forest Regressor"
        }

sim_state = SimulationState()


def process_mqtt_telemetry(payload_dict):
    """Processes incoming MQTT telemetry payload from any of 5 PLCs through Random Forest ML pipeline."""
    try:
        plc_id = int(payload_dict.get("plc_id", 1))
        temp = float(payload_dict.get("temperature", payload_dict.get("Temperature", 62.0)))
        vib = float(payload_dict.get("vibration", payload_dict.get("Vibration", 0.2)))
        curr = float(payload_dict.get("motor_current", payload_dict.get("Motor_Current", 8.0)))
        press = float(payload_dict.get("pressure", payload_dict.get("Pressure", 5.0)))
        noise = float(payload_dict.get("noise", payload_dict.get("Noise", payload_dict.get("Acoustic_Noise", 42.0))))
        health = float(payload_dict.get("Machine_Health", payload_dict.get("health", 100.0)))
        active_event = str(payload_dict.get("Active_Event", "None"))
        ts = str(payload_dict.get("timestamp", payload_dict.get("Timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))))

        # 1. Isolation Forest Anomaly Detection
        anomaly_res = model_service.detect_anomaly(temp, vib, curr, pressure=press, noise=noise)
        is_anomaly = anomaly_res["is_anomaly"]
        anomaly_status = anomaly_res["anomaly_status"]
        
        # Deviation calculation
        t_dev = max(0.0, (temp - 62.0) / 15.0)
        v_dev = max(0.0, (vib - 0.20) / 4.0)
        c_dev = max(0.0, (curr - 8.0) / 7.2)
        p_dev = max(0.0, (press - 5.0) / 3.0)
        n_dev = max(0.0, (noise - 42.0) / 30.0)
        sensor_anomaly_score = 0.25 * t_dev + 0.30 * v_dev + 0.15 * c_dev + 0.15 * p_dev + 0.15 * n_dev

        # 2. Random Forest RUL Prediction
        raw_pred_rul, model_used, raw_pred_float, confidence_pct, ci = model_service.predict_rul(
            temp, vib, curr, pressure=press, noise=noise, return_full_info=True
        )

        prev_rul = sim_state.prev_displayed_rul.get(plc_id, None)
        val_float, displayed_rul = filter_displayed_rul(
            raw_prediction=raw_pred_rul,
            prev_displayed_rul=prev_rul,
            health=health
        )
        sim_state.prev_displayed_rul[plc_id] = val_float

        # 3. Decision Engine
        prev_level = sim_state.prev_status_level.get(plc_id, 0)
        maint_info = get_maintenance_recommendation(
            predicted_rul=displayed_rul,
            machine_health=health,
            active_event=active_event,
            max_lifespan_days=250,
            prev_status_level=prev_level,
            sensor_anomaly_score=sensor_anomaly_score,
            is_anomaly=is_anomaly
        )
        sim_state.prev_status_level[plc_id] = maint_info.get("status_level", 0)

        record = {
            "plc_id": plc_id,
            "timestamp": ts,
            "Timestamp": ts,
            "temperature": round(temp, 1),
            "vibration": round(vib, 2),
            "motor_current": round(curr, 1),
            "pressure": round(press, 1),
            "noise": round(noise, 1),
            "Temperature": temp,
            "Vibration": vib,
            "Motor_Current": curr,
            "Pressure": press,
            "Noise": noise,
            "Machine_Health": round(health, 1),
            "machine_health": round(health, 1),
            "Machine_Status": maint_info["maintenance_status"],
            "machine_status": maint_info["maintenance_status"],
            "Machine_Condition": maint_info["machine_condition"],
            "machine_condition": maint_info["machine_condition"],
            "Failure_Risk_Pct": maint_info["failure_risk_pct"],
            "failure_risk_pct": maint_info["failure_risk_pct"],
            "Anomaly_Status": anomaly_status,
            "anomaly_status": anomaly_status,
            "Anomaly_Score": anomaly_res["anomaly_score"],
            "Prediction_Confidence": confidence_pct,
            "prediction_confidence": confidence_pct,
            "Model_Used": model_used,
            "model_used": model_used,
            "Predicted_RUL": displayed_rul,
            "predicted_rul_days": displayed_rul,
            "actual_rul_days": int(payload_dict.get("Remaining_Useful_Life_Days", 250)),
            "Remaining_Useful_Life_Days": int(payload_dict.get("Remaining_Useful_Life_Days", 250)),
            "Recommended_Action": maint_info["recommended_action"],
            "Inspection_Priority": maint_info["inspection_priority"],
            "Next_Inspection_Window": maint_info["next_inspection_window"],
            "Active_Event": active_event
        }

        sim_state.plc_records[plc_id] = record
        sim_state.history_records.append(record)
        if len(sim_state.history_records) > 1000:
            sim_state.history_records.pop(0)

        logger.info(f"MQTT Received PLC {plc_id} | Temp: {temp} | Vib: {vib} | RUL Pred (RF): {displayed_rul} Days")
        return record

    except Exception as e:
        logger.error(f"Error processing MQTT telemetry payload: {e}", exc_info=True)


# MQTT Backend Subscriber Thread
class BackendMqttSubscriber:
    def __init__(self, broker="broker.hivemq.com", port=1883):
        self.broker = broker
        self.port = port
        self.client = None

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        brokers_to_try = [(self.broker, self.port), ("127.0.0.1", 1883)]
        for host, port in brokers_to_try:
            try:
                try:
                    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="Backend_MQTT_Subscriber")
                except Exception:
                    c = mqtt.Client(client_id="Backend_MQTT_Subscriber")
                
                c.on_connect = self.on_connect
                c.on_message = self.on_message
                c.connect(host, port, keepalive=60)
                c.loop_start()
                self.client = c
                logger.info(f"MQTT Subscriber connected successfully to {host}:{port}")
                break
            except Exception as e:
                logger.warning(f"MQTT Subscriber connection to {host}:{port} failed: {e}")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        logger.info("MQTT Subscriber connected to broker. Subscribing to plc/#...")
        client.subscribe("plc/#")

    def on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
            process_mqtt_telemetry(data)
        except Exception as e:
            logger.error(f"Error processing MQTT message on topic {msg.topic}: {e}")

mqtt_sub = BackendMqttSubscriber()


def generate_next_telemetry_step():
    record = sim_engine.step()
    return process_mqtt_telemetry(record)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not sim_state.history_records:
        generate_next_telemetry_step()
    mqtt_sub.start()
    yield

app = FastAPI(
    title="AI-Based Predictive Maintenance Platform",
    description="Digital Twin SCADA & Predictive Maintenance ML Engine with Random Forest Regressor & Isolation Forest",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

frontend_dist = os.path.join(base_dir, "frontend", "dist")
assets_dir = os.path.join(frontend_dist, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/api/status")
def get_status():
    try:
        return {
            "status": "online",
            "machine_id": "MCH-802X",
            "machine_name": "Turbine Motor Unit A1",
            "data_source": "5-PLC MQTT Telemetry Engine (broker.hivemq.com:1883)",
            "model": model_service.best_model_name,
            "available_models": ["Random Forest Regressor"],
            "active_plcs": [1, 2, 3, 4, 5],
            "features": ["Temperature", "Vibration", "Motor Current", "Pressure", "Noise"],
            "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Error in GET /api/status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch system status: {str(e)}")


@app.get("/api/plcs")
def get_all_plcs():
    try:
        plcs_data = []
        for plc_id in range(1, 6):
            rec = sim_state.get_plc_status(plc_id)
            plcs_data.append(rec)
        return {"plcs": plcs_data}
    except Exception as e:
        logger.error(f"Error in GET /api/plcs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch PLC status: {str(e)}")


@app.get("/api/current")
def get_current(plc_id: int = 1):
    try:
        machines_data = []
        for pid in range(1, 6):
            rec = sim_state.get_plc_status(pid)
            machines_data.append({
                "plc_id": pid,
                "temperature": round(float(rec.get("temperature", 62.0)), 1),
                "vibration": round(float(rec.get("vibration", 0.2)), 2),
                "motor_current": round(float(rec.get("motor_current", 8.0)), 1),
                "pressure": round(float(rec.get("pressure", 5.0)), 1),
                "noise": round(float(rec.get("noise", 42.0)), 1),
                "predicted_rul_days": int(rec.get("predicted_rul_days", 200)),
                "machine_status": str(rec.get("machine_status", "Healthy")),
                "anomaly_status": str(rec.get("anomaly_status", "Normal"))
            })
            
        row = sim_state.get_plc_status(plc_id)
        temp = float(row.get("temperature", 62.0))
        vib = float(row.get("vibration", 0.2))
        curr = float(row.get("motor_current", 8.0))
        press = float(row.get("pressure", 5.0))
        noise = float(row.get("noise", 42.0))
        health = float(row.get("machine_health", 100.0))
        predicted_rul = int(row.get("predicted_rul_days", 0))
        machine_status = str(row.get("machine_status", "Healthy"))
        machine_condition = str(row.get("machine_condition", "Healthy"))
        anomaly_status = str(row.get("anomaly_status", "Normal"))
        failure_risk = float(row.get("failure_risk_pct", 0.0))
        confidence = float(row.get("prediction_confidence", 95.0))
        model_used = str(row.get("model_used", model_service.best_model_name))
        
        return {
            "machines": machines_data,
            "plc_id": plc_id,
            "current_idx": len(sim_state.history_records) - 1,
            "total_records": max(1000, len(sim_state.history_records)),
            "timestamp": str(row.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
            "temperature": round(temp, 2),
            "vibration": round(vib, 2),
            "motor_current": round(curr, 2),
            "pressure": round(press, 2),
            "noise": round(noise, 2),
            "machine_health": round(health, 1),
            "machine_status": machine_status,
            "machine_condition": machine_condition,
            "predicted_rul_days": predicted_rul,
            "actual_rul_days": int(row.get("actual_rul_days", 250)),
            "failure_risk_pct": round(failure_risk, 1),
            "anomaly_status": anomaly_status,
            "prediction_confidence": round(confidence, 1),
            "model_used": model_used
        }
    except Exception as e:
        logger.error(f"Error in GET /api/current: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch telemetry state: {str(e)}")


@app.get("/api/history")
def get_history(plc_id: int = None):
    try:
        records = sim_state.history_records
        if plc_id is not None:
            records = [r for r in records if r.get("plc_id") == plc_id]
        if not records:
            records = [sim_state.get_plc_status(plc_id or 1)]
            
        return {
            "history": records[-100:],
            "total_records": len(records)
        }
    except Exception as e:
        logger.error(f"Error in GET /api/history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch history telemetry: {str(e)}")


@app.get("/api/maintenance")
def get_maintenance_status(plc_id: int = 1):
    try:
        row = sim_state.get_plc_status(plc_id)
        
        temp = float(row.get("temperature", 62.0))
        vib = float(row.get("vibration", 0.2))
        curr = float(row.get("motor_current", 8.0))
        press = float(row.get("pressure", 5.0))
        noise = float(row.get("noise", 42.0))
        health = float(row.get("machine_health", 100.0))
        predicted_rul = int(row.get("predicted_rul_days", 0))
        machine_status = str(row.get("machine_status", "Healthy"))
        machine_condition = str(row.get("machine_condition", "Healthy"))
        anomaly_status = str(row.get("anomaly_status", "Normal"))
        failure_risk = float(row.get("failure_risk_pct", 0.0))
        
        return {
            "plc_id": plc_id,
            "machine_health": round(health, 1),
            "machine_status": machine_status,
            "machine_condition": machine_condition,
            "anomaly_status": anomaly_status,
            "failure_risk_pct": failure_risk,
            "predicted_rul_days": predicted_rul,
            "recommended_action": str(row.get("Recommended_Action", "No action required")),
            "inspection_priority": str(row.get("Inspection_Priority", "Low")),
            "next_inspection_window": str(row.get("Next_Inspection_Window", "Routine inspection within 90-120 days")),
            "timestamp": str(row.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))),
            "temperature": round(temp, 2),
            "vibration": round(vib, 2),
            "motor_current": round(curr, 2),
            "pressure": round(press, 2),
            "noise": round(noise, 2)
        }
    except Exception as e:
        logger.error(f"Error in GET /api/maintenance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch maintenance status: {str(e)}")


class PredictRequest(BaseModel):
    temperature: float = Field(..., ge=-50.0, le=250.0, description="Operating temperature in deg C")
    vibration: float = Field(..., ge=0.0, le=50.0, description="Vibration amplitude in mm/s")
    motor_current: float = Field(..., ge=0.0, le=100.0, description="Motor current in Amperes")
    pressure: float = Field(default=5.0, ge=0.0, le=1000.0, description="Pressure reading in bar")
    noise: float = Field(default=42.0, ge=0.0, le=200.0, description="Acoustic noise in dB")
    model: str = Field(default="auto", description="Model selector: 'Random Forest Regressor' or 'auto'")

@app.post("/api/predict")
def predict_rul(req: PredictRequest):
    try:
        rul, model_name, raw_pred, confidence, ci = model_service.predict_rul(
            req.temperature,
            req.vibration,
            req.motor_current,
            pressure=req.pressure,
            noise=req.noise,
            model_name=req.model,
            return_full_info=True
        )
        anomaly_info = model_service.detect_anomaly(
            req.temperature,
            req.vibration,
            req.motor_current,
            pressure=req.pressure,
            noise=req.noise
        )
        return {
            "predicted_rul": rul,
            "model": model_name,
            "raw_prediction": round(raw_pred, 2),
            "confidence_pct": confidence,
            "confidence_interval": ci,
            "anomaly_status": anomaly_info["anomaly_status"],
            "is_anomaly": anomaly_info["is_anomaly"]
        }
    except Exception as e:
        logger.error(f"Error in POST /api/predict: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate RUL prediction: {str(e)}")

@app.get("/api/model")
def get_model_evaluation():
    try:
        comp_data = model_service.get_comparison_data()
        if comp_data:
            return comp_data
        raise HTTPException(status_code=500, detail="Model evaluation metadata not loaded. Please train models first.")
    except Exception as e:
        logger.error(f"Error in GET /api/model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch model metrics: {str(e)}")


@app.get("/api/logs")
def get_logs(plc_id: int = None):
    try:
        records = sim_state.history_records
        if plc_id is not None:
            records = [r for r in records if r.get("plc_id") == plc_id]
        recent = records[-10:] if records else []
        logs = []
        for r in recent:
            temp = float(r.get("temperature", 62.0))
            vib = float(r.get("vibration", 0.2))
            curr = float(r.get("motor_current", 8.0))
            press = float(r.get("pressure", 5.0))
            noise = float(r.get("noise", 42.0))
            health = float(r.get("machine_health", 100.0))
            pred_rul = int(r.get("predicted_rul_days", 0))
            status, _ = get_status_color(health)
            
            logs.append({
                "plc_id": r.get("plc_id", 1),
                "timestamp": str(r.get("timestamp", "")),
                "temperature": round(temp, 2),
                "vibration": round(vib, 2),
                "motor_current": round(curr, 2),
                "pressure": round(press, 2),
                "noise": round(noise, 2),
                "predicted_rul": pred_rul,
                "machine_health": round(health, 1),
                "machine_condition": r.get("machine_condition", "Healthy"),
                "anomaly_status": r.get("anomaly_status", "Normal"),
                "failure_risk_pct": r.get("failure_risk_pct", 0.0),
                "status": status,
                "active_event": r.get("Active_Event", "None")
            })
            
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Error in GET /api/logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch recent logs: {str(e)}")


class ControlAction(BaseModel):
    action: str = Field(..., pattern="^(start|pause|next|reset|set_speed)$")
    speed: float = Field(default=1.0, ge=0.05, le=10.0)

@app.post("/api/control")
def control_simulation(action: ControlAction):
    try:
        if action.action == "reset":
            sim_state.reset()
        elif action.action == "set_speed":
            sim_state.simulation_speed = action.speed
                
        return {
            "current_idx": len(sim_state.history_records) - 1,
            "auto_play": sim_state.auto_play,
            "simulation_speed": sim_state.simulation_speed
        }
    except Exception as e:
        logger.error(f"Error in POST /api/control: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process control action: {str(e)}")


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.svg", include_in_schema=False)
def get_favicon():
    fav_svg = os.path.join(frontend_dist, "favicon.svg")
    if os.path.exists(fav_svg):
        return FileResponse(fav_svg, media_type="image/svg+xml")
    fav_ico = os.path.join(frontend_dist, "favicon.ico")
    if os.path.exists(fav_ico):
        return FileResponse(fav_ico, media_type="image/x-icon")
    return Response(status_code=204)

@app.get("/icons.svg", include_in_schema=False)
def get_icons():
    icons_path = os.path.join(frontend_dist, "icons.svg")
    if os.path.exists(icons_path):
        return FileResponse(icons_path, media_type="image/svg+xml")
    return Response(status_code=404)

@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str):
    safe_path = os.path.normpath(os.path.join(frontend_dist, full_path))
    if safe_path.startswith(frontend_dist) and os.path.isfile(safe_path):
        return FileResponse(safe_path)
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse(
        status_code=404,
        content={"detail": "Frontend build not found. Run 'npm run build' in the frontend directory."}
    )

if __name__ == "__main__":
    reload_flag = os.getenv("UVICORN_RELOAD", "false").lower() in ("true", "1", "yes")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=reload_flag, timeout_keep_alive=65)
