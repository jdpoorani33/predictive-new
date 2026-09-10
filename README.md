# AI-Based Predictive Maintenance System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.0-61DAFB.svg)](https://react.dev/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4.0-F7931E.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end industrial **AI-Based Predictive Maintenance & Digital Twin SCADA System** designed for high-uptime rotating machinery and turbine motor units. The platform delivers **multi-model Remaining Useful Life (RUL) regression**, **unsupervised anomaly detection**, **real-time machine condition monitoring**, **dynamic failure risk scoring**, and **decision-support maintenance planning** using 5 primary physical sensor channels.

---

## 1. Project Overview

Industrial downtime resulting from unexpected equipment breakdown accounts for billions of dollars in unscheduled maintenance and lost throughput annually. This project provides a production-grade predictive maintenance platform that replaces traditional reactive and calendar-based servicing with continuous, sensor-driven condition monitoring and machine learning diagnostics.

The system combines:
- A stochastic **Digital Twin SCADA Simulator** generating live 5-sensor industrial telemetry.
- A **FastAPI** asynchronous backend executing real-time inference across 3 RUL regression models and an Isolation Forest anomaly detector.
- A modern **React 18 + Tailwind CSS** dashboard featuring live SCADA gauges, interactive trend plots, maintenance schedule matrices, and comparative model diagnostic charts.

---

## 2. Problem Statement

In industrial manufacturing, plant operators struggle to answer three critical operational questions:
1. **When will the asset fail?** (Predicting Remaining Useful Life with confidence intervals).
2. **Is the asset currently operating abnormally?** (Detecting out-of-distribution sensor spikes before physical failure occurs).
3. **What specific maintenance action is required today?** (Translating raw telemetry into prioritized servicing actions and scheduling).

Traditional threshold alarms create false alarm fatigue and fail to identify gradual multi-variable degradation patterns. This system solves these problems by modeling multi-sensor cross-correlations and physical wear progression over time.

---

## 3. Objectives

- Predict machine **Remaining Useful Life (RUL) measured in Days** with quantified uncertainty and confidence intervals.
- Detect **operational anomalies** in real time using unsupervised tree-isolation techniques.
- Continuously compute a data-driven **Health Index (0% – 100%)** and **Failure Risk (0% – 100%)** from live sensor telemetry.
- Provide a fair, identical-split benchmark comparing **Random Forest Regressor**, ****, and ****.
- Deliver an operator-friendly SCADA dashboard with interactive simulation controls, maintenance scheduling, and model diagnostics.

---

## 4. Key Features

- **Multi-Model Regression Suite**: Benchmarks **Random Forest**, ****, and **** on identical holdout test sets with automated Best Model selection.
- **Machine Anomaly Detection**: Unsupervised **Isolation Forest** scoring for instantaneous detection of mechanical or electrical overload states.
- **Dynamic Health Index & Failure Risk**: Continuous mathematical models that dynamically track temperature, vibration, current, pressure, and noise wear progression.
- **Machine Condition Classification**: Tri-state condition tagging (**Healthy**, **Warning**, **Critical**) with descriptive operational stages (**Healthy**, **Slight Wear**, **Moderate Wear**, **Critical**, **Failure**).
- **Interactive SCADA Digital Twin**: Real-time simulation clock with speed multiplier (1x–10x), manual single-step advancement, pause, and fresh state reset.
- **Plotly Diagnostic Visualizations**: Feature importance bar charts, actual vs. predicted scatter plots with 1:1 reference lines, and residual error histograms.
- **Maintenance Decision Support**: Actionable maintenance recommendations, inspection priority ranking, and estimated servicing costs.

---

## 5. System Architecture

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                Real-Time Machine Simulator                  │
 │          (Digital Twin SCADA: 5 Correlated Sensors)         │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                     FastAPI REST Backend                    │
 │                                                             │
 │  ┌─────────────────────────┐   ┌─────────────────────────┐  │
 │  │ Preprocessing & Scaler  │   │ Isolation Forest Engine │  │
 │  │   (5 Sensor Features)   │   │   (Anomaly Detection)   │  │
 │  └───────────┬─────────────┘   └────────────┬────────────┘  │
 │              │                              │               │
 │              ▼                              ▼               │
 │  ┌───────────────────────────────────────────────────────┐  │
 │  │                RUL Regression Models                  │  │
 │  │  • Random Forest  •   •       │  │
 │  └───────────────────────────┬───────────────────────────┘  │
 │                              │                              │
 │                              ▼                              │
 │  ┌───────────────────────────────────────────────────────┐  │
 │  │ Maintenance Engine (Health Index, Risk, Condition)    │  │
 │  └───────────────────────────┬───────────────────────────┘  │
 └──────────────────────────────┼──────────────────────────────┘
                                │ JSON REST APIs
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                   React 18 + Vite Frontend                  │
 │  ┌───────────────┐ ┌───────────────┐ ┌───────────────────┐  │
 │  │ Live SCADA    │ │ Analytics     │ │ Maintenance       │  │
 │  │ Dashboard     │ │ Lifecycle     │ │ Decision Support  │  │
 │  └───────────────┘ └───────────────┘ └───────────────────┘  │
 │  ┌───────────────────────────────────────────────────────┐  │
 │  │ Model Evaluation & 3-Model Benchmark Comparison       │  │
 │  └───────────────────────────────────────────────────────┘  │
 └─────────────────────────────────────────────────────────────┘
```

---

## 6. Machine Learning Models

### 1. Random Forest Regressor (Baseline Model)
- **Implementation**: `sklearn.ensemble.RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)`
- **Strengths**: Robust to non-linear sensor interactions, resilient to localized noise, ensemble tree variance yields meaningful prediction confidence intervals.
- **Performance**: Test $R^2 = 0.8929$ | MAE = $25.46\text{ Days}$ | RMSE = $34.81\text{ Days}$ (**★ Best Model**).

### 2.  (Added Model)
- **Strengths**: Sequential error reduction focusing on difficult transitional degradation zones; high generalization stability.
- **Performance**: Test $R^2 = 0.8918$ | MAE = $25.86\text{ Days}$ | RMSE = $34.99\text{ Days}$.

### 3.  (Added Model)
- **Performance**: Test $R^2 = 0.8921$ | MAE = $25.87\text{ Days}$ | RMSE = $34.94\text{ Days}$.

### 4. Isolation Forest (Machine Anomaly Detection)
- **Implementation**: `sklearn.ensemble.IsolationForest(n_estimators=100, contamination=0.05, random_state=42)`
- **Function**: Evaluates multi-dimensional sensor space to isolate anomalous outliers without requiring labeled failure datasets. Output: `"Normal"` vs `"Anomaly Detected"`.

---

## 7. Input Features

All regression models and the anomaly detector utilize the same **5 physical sensor channels**:

| Feature Name | Column Identifier | Engineering Unit | Normal Baseline Range | Sensor Description |
| :--- | :--- | :--- | :--- | :--- |
| **Temperature** | `Temperature` | °C | $60.0 - 64.0\text{ °C}$ | Core motor winding & stator surface temperature |
| **Vibration** | `Vibration` | RMS mm/s | $0.15 - 0.25\text{ mm/s}$ | Tri-axial velocity vibration sensor tracking bearing wear |
| **Motor Current** | `Motor_Current` | Amperes (A) | $7.8 - 8.2\text{ A}$ | Active phase current drawn under operating mechanical load |
| **Pressure** | `Pressure` | bar | $4.8 - 5.2\text{ bar}$ | Lubricant oil circulation & pneumatic system pressure |
| **Noise** | `Noise` | dB (Acoustic) | $40.0 - 44.0\text{ dB}$ | Acoustic sound pressure emissions detecting cavitation/chatter |

---

## 8. Prediction / RUL Functionality

- **Target Variable**: `Remaining_Useful_Life_Days` (**RUL in Days**).
- **Prediction Pipeline**:
  1. 5 raw sensor readings are forwarded through `StandardScaler` fitted only on training data.
  2. The active model (`Random Forest`, ``, ``, or `Best Model`) generates a point estimate in continuous days.
  3. Prediction is clipped at $0\text{ Days}$ (preventing negative values) and rounded to integer days.
  4. Standard error derived from ensemble tree variance computes the 95% confidence interval $[RUL_{lower}, RUL_{upper}]$ and confidence percentage (e.g., $97.1\%$).

---

## 9. Anomaly Detection

- The **Isolation Forest** computes an anomaly score based on the average path length required to isolate a telemetry point in random trees.
- Normal operation produces positive decision values tagged as `"Normal"`.
- Severe sensor spikes (e.g., Temperature $> 95\text{ °C}$, Vibration $> 4.0\text{ mm/s}$) produce negative decision values tagged as `"Anomaly Detected"`.
- An active anomaly automatically penalizes the **Failure Risk** score and escalates **Machine Condition** to `Warning` or `Critical`.

---

## 10. Root Cause Analysis

### Health Index & Machine Condition Calculation Chain
The system derives machine status through a fully explainable, multi-stage calculation chain:
```text
Live Sensor Telemetry (T, V, C, P, N)
        ↓
Deviation from Healthy Baseline (d_temp, d_vib, d_curr, d_press, d_noise)
        ↓
Monotonic Physical Cumulative Wear (cum_wear)
        ↓
Dynamic Health Index (%) = 100.0 - (Age_Decay + Wear_Decay * 87.0)
        ↓
Dynamic Failure Risk (%) = 0.60 * (100 - Health) + 0.40 * (1 - RUL/Lifespan)*100 + Anomaly_Penalty
        ↓
Machine Condition Classification (Healthy / Warning / Critical)
        ↓
Maintenance Decision Recommendation & Servicing Window
```

- **Why Health Index Decreases Over Time**: As the machine accumulates operational hours, thermal and vibrational deviations grow, driving cumulative wear monotonically upwards.
- **Healthy vs Degraded State**: At Day 1, Health is $99.9\%$ (`Healthy`). By Day 170+, gradual wear brings Health to $\sim 54.6\%$ (`Moderate Wear / Warning`). Near the end of life, Health drops below $25\%$ (`Critical`).

---

## 11. Real-Time Machine Simulation

The **Digital Twin SCADA Simulator** (`simulator/simulator.py`) models a realistic 365-day physical machine life cycle:
- **Stationary Brownian Drift**: Low-frequency stochastic random walk preventing artificial flat lines.
- **Diurnal Oscillations**: Thermal and load cycles reflecting daily factory operating patterns.
- **Correlated Multi-Sensor Coupling**: Thermal spikes dynamically increase electrical current and line pressure; bearing vibration couples to acoustic noise.
- **Heteroskedastic Noise**: Variance expands as equipment ages and mechanical tolerances loosen.
- **Coupled Overload Bursts**: Intermittent thermal bursts and vibration peaks in degrading phases.

---

## 12. Dashboard Features

- **Top System Summary Banner**: Displays live **Machine Condition** badge, **Isolation Forest Anomaly** status, **Failure Risk %**, **RUL Confidence %**, and active ML model.
- **Radial SVG Health Gauge**: Color-shifting indicator transitioning smoothly across Green ($\ge 80\%$), Blue ($60-79\%$), Yellow ($40-59\%$), Orange ($15-39\%$), and Red ($<15\%$).
- **5 Sensor Telemetry Cards**: Real-time readouts for Temperature, Vibration, Motor Current, Pressure, and Noise with engineering units.
- **Interactive Live Chart**: Single large SVG plot with parameter dropdown, historical trendline, and forward-looking polynomial forecast.
- **Recent Sensor Readings Table**: Tabular log of the last 10 telemetry steps with timestamp, 5 sensor readings, predicted RUL, health index, anomaly status, and operational stage.
- **Multi-Model Benchmark Diagnostics**: Comparative performance table, diagnostic model selector, 6 KPI cards, and dynamic Plotly diagnostic charts.

---

## 13. Backend API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | System operational state, active model, available models, and feature list |
| `GET` | `/api/current` | Latest live telemetry reading, 5 sensors, health index, RUL, condition, anomaly |
| `GET` | `/api/history` | Historical telemetry records (default: last 50 steps) for trend visualization |
| `GET` | `/api/maintenance` | Maintenance status, priority level, recommended action, next inspection date |
| `GET` | `/api/model` | Benchmark comparison table, best model identifier, and diagnostic chart data |
| `GET` | `/api/logs` | Latest 10 operational log records for table view |
| `POST` | `/api/predict` | Manual RUL inference and anomaly check for custom 5-sensor input payloads |
| `POST` | `/api/control` | Simulation controls: `start`, `pause`, `step`, `reset`, `set_speed` |

---

## 14. Technology Stack

- **Backend**: Python 3.10+, FastAPI 0.110.0, Uvicorn, Pydantic 2.7
- **Machine Learning**: Scikit-Learn 1.4.0,  2.0.0+, Pandas 2.2, NumPy 1.26, Joblib 1.4
- **Frontend**: React 18, Vite 8, Tailwind CSS, Lucide React, React-Plotly.js, Axios
- **Architecture**: RESTful Client-Server, Digital Twin SCADA Simulation, Pre-compiled Single-Port Deployment

---

## 15. Project Structure

```text
industrial-predictive-maintenance/
├── datasets/                 # 91,250 multi-sensor records and data generator
│   └── sensor_data.csv
├── models/                   # Serialized ML model binaries and benchmark JSON
│   ├── rf_rul_model.pkl
│   ├── isolation_forest.pkl
│   ├── scaler.pkl
│   └── model_comparison.json
├── model/                    # Model training, inference, and maintenance logic
│   ├── train_model.py
│   ├── predict.py
│   └── maintenance_engine.py
├── preprocessing/            # 5-feature extraction and rolling feature tools
│   └── preprocessing.py
├── simulator/                # Digital twin real-time SCADA simulation engine
│   └── simulator.py
├── frontend/                 # React 18 + Vite frontend source code
│   ├── src/
│   │   ├── pages/            # Dashboard, Analytics, Maintenance, Evaluation
│   │   └── components/       # Gauges, charts, tables, model evaluation view
│   └── dist/                 # Pre-built production assets served by FastAPI
├── main.py                   # FastAPI backend server entry point
├── requirements.txt          # Python package requirements
├── PROJECT_STRUCTURE.md      # Detailed file-by-file structural documentation
└── README.md                 # Complete system guide & documentation
```

---

## 16. Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YourUsername/industrial-predictive-maintenance.git
cd industrial-predictive-maintenance
```

### 2. Create and Activate Virtual Environment
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 17. How to Run the Backend

Launch the FastAPI application server:
```bash
# Windows
python main.py

# Or with uvicorn directly
uvicorn main.py:app --host 127.0.0.1 --port 8000 --reload
```

The application will start at **`http://127.0.0.1:8000`**.

---

## 18. How to Run the Frontend

The FastAPI backend automatically serves the pre-compiled production frontend from `frontend/dist/` at `http://127.0.0.1:8000`.

To run the Vite development server independently with hot-reloading:
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 19. Model Training

To retrain all 3 regression models, the Isolation Forest anomaly detector, and re-compute holdout benchmarks:
```bash
python model/train_model.py
```

Output:
```text
==================================================
 Predictive Maintenance ML Training Pipeline
 (Random Forest +  +  + Isolation Forest)
==================================================
1. Loading dataset...
   Dataset size: 91,250 records
   Input features (5): ['Temperature', 'Vibration', 'Motor_Current', 'Pressure', 'Noise']
   Target variable: Remaining_Useful_Life_Days (RUL in Days)

2. Preprocessing data & 80/20 train-test split...
   Training records: 73,000
   Testing records:  18,250

3. Training & Evaluating 3 Regression Models on Identical Split:
   -> Training Random Forest Regressor...
      Train R²: 0.9054 | Test R²: 0.8929 | MAE: 25.46 Days | RMSE: 34.81 Days
   -> Training ...
      Train R²: 0.8989 | Test R²: 0.8918 | MAE: 25.86 Days | RMSE: 34.99 Days
   -> Training ...
      Train R²: 0.8992 | Test R²: 0.8921 | MAE: 25.87 Days | RMSE: 34.94 Days

4. Training Isolation Forest for Machine Anomaly Detection...
   Isolation Forest saved to: models/isolation_forest.pkl

 Best Model Identified: Random Forest Regressor (Lowest RMSE = 34.81 Days)
==================================================
```

---

## 20. Model Evaluation

Holdout validation results on the 18,250 untouched test records:

| Model | MAE (Days) | RMSE (Days) | $R^2$ Score (Test) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Random Forest Regressor** | **25.46** | **34.81** | **0.8929** | ★ **Best Model (Lowest RMSE)** |
| **** | **25.87** | **34.94** | **0.8921** | Optimal Regularization |
| **** | **25.86** | **34.99** | **0.8918** | High Generalization |

All metrics and diagnostic plots are dynamically generated from holdout predictions without any hardcoded values.

---

## 21. Example API Request

### Predict RUL for Custom Sensor Input:
```bash
curl -X POST "http://127.0.0.1:8000/api/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "temperature": 74.5,
       "vibration": 0.85,
       "motor_current": 10.2,
       "pressure": 6.1,
       "noise": 52.0,
       "model": ""
     }'
```

### JSON Response:
```json
{
  "predicted_rul": 138,
  "raw_prediction": 138.42,
  "confidence_pct": 92.4,
  "confidence_interval": [128.8, 148.0],
  "model_used": "",
  "anomaly_status": "Normal",
  "is_anomaly": false,
  "anomaly_score": 0.128,
  "machine_condition": "Healthy",
  "failure_risk_pct": 14.8,
  "maintenance_recommendation": "Continue normal operation. Machine parameters within optimal nominal limits."
}
```

---

## 22. Future Enhancements

- [ ] Add MQTT / OPC-UA protocol ingestion adapter for real physical PLC connections.
- [ ] Implement LSTM / Temporal Fusion Transformer (TFT) deep learning models for sequence modeling.
- [ ] Add automated SMS / Webhook / Email alert notifications for critical failure risk threshold breaches.
- [ ] Introduce multi-machine fleet management overview page.

---

## 23. Limitations

- The real-time telemetry stream is powered by a high-fidelity mathematical digital twin model rather than a live physical machine hardware bus.
- Prediction accuracy is optimized for continuous industrial rotating equipment (motors, pumps, turbines) with 5 primary telemetry channels.

---

## 24. Author

- **AI & Predictive Maintenance Engineer**: Project Developer
- **Repository**: [https://github.com/YourUsername/industrial-predictive-maintenance](https://github.com/YourUsername/industrial-predictive-maintenance)
- **License**: [MIT License](LICENSE)
