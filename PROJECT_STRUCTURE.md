# Project Structure & Architecture

This document provides a detailed breakdown of the directory organization, module responsibilities, and data flows within the **AI-Based Predictive Maintenance System**.

---

## 1. Directory Tree

```text
industrial-predictive-maintenance/
│
├── datasets/                            # Dataset storage and synthetic data generator
│   ├── sensor_data.csv                  # 91,250 multi-sensor IoT telemetry records (250 machines × 365 days)
│   └── dataset_generator.py             # Script to generate physical twin sensor datasets
│
├── data/                                # Backup / legacy dataset mirror
│   └── sensor_data.csv                  # Secondary dataset copy
│
├── models/                              # Trained machine learning model artifacts & diagnostics
│   ├── rf_rul_model.pkl                 # Trained Random Forest Regressor (Baseline RUL model)
│   ├── random_forest_model.pkl          # Alias link for Random Forest Regressor
│   ├── _model.pkl                # Trained  (Added RUL model)
│   ├── isolation_forest.pkl             # Trained Isolation Forest (Machine Anomaly Detection)
│   ├── isolation_forest_model.pkl       # Alias link for Isolation Forest
│   ├── scaler.pkl                       # StandardScaler fitted exclusively on training set
│   ├── model_comparison.json            # Dynamic benchmark comparison metadata (MAE, RMSE, R²)
│   └── model_metrics.json               # Default / best model diagnostic metrics & residual plots
│
├── model/                               # ML model source code & logic
│   ├── train_model.py                   # Multi-model training and holdout evaluation pipeline
│   ├── predict.py                       # PredictiveMaintenanceModel inference & anomaly detection engine
│   └── maintenance_engine.py            # Multi-factor maintenance decision logic & condition classification
│
├── preprocessing/                       # Data loading and feature engineering
│   └── preprocessing.py                 # 5-feature extraction, causal rolling stats, 80/20 train/test split
│
├── simulator/                           # Industrial SCADA digital twin simulation
│   └── simulator.py                     # RealTimeMachineSimulator with Brownian drift, wear & sensor coupling
│
├── utils/                               # Shared formatting and status helpers
│   └── utils.py                         # Health status color mapping and badge helpers
│
├── frontend/                            # React 18 + Vite + Tailwind CSS dashboard application
│   ├── index.html                       # Frontend HTML entry point
│   ├── package.json                     # NPM packages & build scripts
│   ├── vite.config.js                   # Vite build and proxy configuration
│   ├── tailwind.config.js               # Tailwind CSS theme and utility configurations
│   ├── src/
│   │   ├── main.jsx                     # React DOM root mounting
│   │   ├── App.jsx                      # Main application container, tab navigation, polling loop
│   │   ├── App.css / index.css          # Styling, scrollbars, and industrial dashboard classes
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx            # Live Monitoring SCADA dashboard (Health, 5 sensors, RUL, condition)
│   │   │   ├── Analytics.jsx            # Multi-sensor lifecycle trend visualization page
│   │   │   ├── Maintenance.jsx          # Predictive maintenance decision support & planning page
│   │   │   └── Evaluation.jsx           # Multi-model diagnostics & benchmark comparison page
│   │   ├── components/
│   │   │   ├── TopBar.jsx               # Header with machine ID, active model badge, online status, clock
│   │   │   ├── Sidebar.jsx              # Navigation tabs and interactive simulation controls
│   │   │   ├── GaugeCard.jsx            # Radial SVG Health Index gauge with smooth color transitions
│   │   │   ├── MetricCard.jsx           # Reusable KPI and sensor telemetry card
│   │   │   ├── LiveChart.jsx            # Interactive parameter dropdown chart with polynomial projection
│   │   │   ├── AnalyticsCharts.jsx      # Multi-parameter trend grid (Temp, Vib, Current, Pressure, Noise, Health)
│   │   │   ├── MaintenanceDashboard.jsx # Maintenance schedule, inspection priority, cost estimates
│   │   │   ├── ModelEvaluation.jsx      # Benchmark comparison table, model selector, diagnostic Plotly charts
│   │   │   ├── SensorTable.jsx          # Live 10-row telemetry table with anomaly indicators
│   │   │   └── StatusBadge.jsx          # Colored operational stage and condition badges
│   │   └── services/
│   │       └── api.js                   # Axios HTTP client connecting to FastAPI backend
│   └── dist/                            # Pre-compiled static assets served by FastAPI
│
├── main.py                              # FastAPI backend application entry point & REST server
├── requirements.txt                     # Python dependencies (scikit-learn, , fastapi, uvicorn, etc.)
├── .gitignore                           # Git ignore rules for clean repository state
├── run_backend.bat                      # Windows batch script to launch backend
├── run_frontend.bat                     # Windows batch script to launch frontend dev server
├── start_app.bat                        # One-click Windows launch script
├── start_app.ps1                        # PowerShell launch script with automatic venv setup
└── README.md                            # Comprehensive project overview, installation, and usage guide
```

---

## 2. Component Descriptions & Roles

### 1. Backend Server & API Entry Point (`main.py`)
- **Framework**: FastAPI + Uvicorn (async ASGI server).
- **Responsibilities**:
  - Serves REST API endpoints (`/api/status`, `/api/current`, `/api/history`, `/api/maintenance`, `/api/predict`, `/api/model`, `/api/logs`, `/api/control`).
  - Manages background simulation clock loop (`simulation_clock_loop`) for real-time telemetry streaming.
  - Implements OWASP security headers (Content-Security-Policy, X-Frame-Options, X-Content-Type-Options).
  - Serves static pre-compiled React frontend for single-port deployment (`http://127.0.0.1:8000`).

### 2. Machine Learning Pipeline (`model/`)
- **`train_model.py`**:
  - Loads 91,250 records from `datasets/sensor_data.csv`.
  - Performs 80/20 train/test split (`73,000` train / `18,250` test with `random_state=42`).
  - Trains:
    1. **Random Forest Regressor** (`n_estimators=100, max_depth=12, random_state=42`)
    2. **** (`n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42`)
    3. **** (`objective="reg:squarederror", n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42`)
    4. **Isolation Forest** (`n_estimators=100, contamination=0.05, random_state=42`)
  - Evaluates models on holdout test set and saves `models/model_comparison.json`.
- **`predict.py`**:
  - Encapsulates `PredictiveMaintenanceModel`.
  - Supports dynamic model selection (`"Random Forest Regressor"`, `""`, `""`, or `"auto"`).
  - Computes prediction confidence and standard error intervals $[RUL_{lower}, RUL_{upper}]$.
  - Evaluates Isolation Forest for real-time anomaly detection.
- **`maintenance_engine.py`**:
  - Single source of truth for maintenance decision support.
  - Classifies `machine_condition`: `Healthy`, `Warning`, `Critical`.
  - Computes dynamic `failure_risk_pct` from health degradation, RUL decay, and anomaly penalties.
  - Recommends actionable servicing windows (`"Continue Normal Operation"`, `"Schedule preventive maintenance"`, `"Immediate maintenance required"`).

### 3. Preprocessing & Feature Engineering (`preprocessing/preprocessing.py`)
- Standardizes 5 primary input features:
  1. `Temperature` (°C)
  2. `Vibration` (RMS mm/s)
  3. `Motor_Current` (A)
  4. `Pressure` (bar)
  5. `Noise` (dB)
- Provides causal rolling window feature calculations (`rolling_mean`, `rolling_std`, `rate_of_change`).
- Fits `StandardScaler` exclusively on the training set to prevent data leakage.

### 4. Digital Twin Simulation Engine (`simulator/simulator.py`)
- Real-time stochastic SCADA digital twin model.
- Models 4 operational lifecycle phases:
  - Phase 1 (Days 1–150): Healthy stationary operation with Brownian micro-drift.
  - Phase 2 (Days 151–260): Gradual onset of mechanical wear and thermal coupling.
  - Phase 3 (Days 261–330): Accelerated wear, vibration oscillations, current peaks.
  - Phase 4 (Days 331–365+): Critical instability, high signal noise, thermal bursts.
- Maintains monotonic physical wear tracking (`cum_wear`) and continuous health decay.

### 5. Frontend Dashboard (`frontend/`)
- Single-page application built with React 18, Vite, Lucide icons, and Plotly.js charts.
- Tabs:
  - **Dashboard**: Real-time SCADA telemetry, condition badge, anomaly badge, Health Index gauge, RUL card with confidence, live trend graph, and 10-step telemetry table.
  - **Analytics**: Multi-sensor lifecycle trend grid with historical readings and polynomial forecast projections.
  - **Maintenance**: Decision matrix, inspection priorities, maintenance schedule, and estimated overhaul cost calculator.
  - **Model Evaluation**: 3-model benchmark comparison table, interactive diagnostic model selector, and dynamic Plotly charts (Feature Importance, Actual vs Predicted scatter, Residual Error histogram).
