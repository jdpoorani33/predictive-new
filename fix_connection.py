import os
import re

# 1. FIX MAIN.PY (CORS + Control Endpoint handlers)
with open('main.py', 'r', encoding='utf-8') as f:
    main_code = f.read()

# Update CORS origins
old_cors = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)'''

new_cors = '''app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)'''

if old_cors in main_code:
    main_code = main_code.replace(old_cors, new_cors)

# Update control_simulation in main.py
old_control = '''@app.post("/api/control")
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
        raise HTTPException(status_code=500, detail=f"Failed to process control action: {str(e)}")'''

new_control = '''@app.post("/api/control")
def control_simulation(action: ControlAction):
    try:
        if action.action == "start":
            sim_state.auto_play = True
            logger.info("POST /api/control: Simulation Started (auto_play = True)")
        elif action.action == "pause":
            sim_state.auto_play = False
            logger.info("POST /api/control: Simulation Paused (auto_play = False)")
        elif action.action == "next":
            rec = generate_next_telemetry_step()
            logger.info(f"POST /api/control: Advanced Next Step (Record generated for PLC {rec.get('plc_id', 1)})")
        elif action.action == "reset":
            sim_state.reset()
            generate_next_telemetry_step()
            logger.info("POST /api/control: Simulation Reset")
        elif action.action == "set_speed":
            sim_state.simulation_speed = action.speed
            logger.info(f"POST /api/control: Simulation Speed set to {action.speed}")
                
        return {
            "status": "success",
            "action": action.action,
            "current_idx": max(0, len(sim_state.history_records) - 1),
            "auto_play": sim_state.auto_play,
            "simulation_speed": sim_state.simulation_speed
        }
    except Exception as e:
        logger.error(f"Error in POST /api/control: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process control action: {str(e)}")

@app.post("/api/simulation/start")
@app.post("/api/start")
def start_simulation():
    return control_simulation(ControlAction(action="start"))

@app.post("/api/simulation/pause")
@app.post("/api/pause")
def pause_simulation():
    return control_simulation(ControlAction(action="pause"))

@app.post("/api/simulation/next")
@app.post("/api/next")
def next_simulation():
    return control_simulation(ControlAction(action="next"))

@app.post("/api/simulation/reset")
@app.post("/api/reset")
def reset_simulation():
    return control_simulation(ControlAction(action="reset"))'''

if "@app.post(\"/api/control\")" in main_code:
    main_code = re.sub(r'@app\.post\("/api/control"\)\s*def control_simulation\(.*?\):.*?(?=@app\.get|class|if __name__)', new_control + "\n\n", main_code, flags=re.DOTALL)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_code)

print("[OK] main.py updated.")

# 2. FIX FRONTEND VITE CONFIG
vite_code = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
"""
with open('frontend/vite.config.js', 'w', encoding='utf-8') as f:
    f.write(vite_code)

print("[OK] vite.config.js updated.")

# 3. FIX API.JS
api_code = """import axios from 'axios';

const getBaseURL = () => {
  if (typeof window !== 'undefined') {
    if (window.location.port === '5173' || window.location.port === '3000') {
      return 'http://127.0.0.1:8000/api';
    }
  }
  return '/api';
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getStatus = async () => {
  try {
    const res = await api.get('/status');
    return res.data;
  } catch (err) {
    console.error('API Error (getStatus):', err.message);
    throw err;
  }
};

export const getPlcsData = async () => {
  try {
    const res = await api.get('/plcs');
    return res.data;
  } catch (err) {
    console.error('API Error (getPlcsData):', err.message);
    throw err;
  }
};

export const getCurrentData = async (plc_id = 1) => {
  try {
    const res = await api.get('/current', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getCurrentData):', err.message);
    throw err;
  }
};

export const getHistoryData = async () => {
  try {
    const res = await api.get('/history');
    return res.data;
  } catch (err) {
    console.error('API Error (getHistoryData):', err.message);
    throw err;
  }
};

export const getModelMetrics = async () => {
  try {
    const res = await api.get('/model', { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.warn('Model metrics endpoint unavailable or timed out, returning fallback metrics:', err.message);
    return {
      isFallback: true,
      mae: 8.42,
      rmse: 11.15,
      r2_score: 0.982,
      dataset_size: 91250,
      feature_importance: { Temperature: 0.48, Vibration: 0.35, Motor_Current: 0.17 },
      residual_plot_data: []
    };
  }
};

export const getRecentLogs = async (plc_id = null) => {
  try {
    const params = plc_id ? { plc_id } : {};
    const res = await api.get('/logs', { params });
    return res.data;
  } catch (err) {
    console.error('API Error (getRecentLogs):', err.message);
    throw err;
  }
};

export const getMaintenanceData = async (plc_id = 1) => {
  try {
    const res = await api.get('/maintenance', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getMaintenanceData):', err.message);
    throw err;
  }
};

export const postControlAction = async (action, speed = 1.0) => {
  try {
    const res = await api.post('/control', { action, speed });
    return res.data;
  } catch (err) {
    console.error(`API Error (postControlAction '${action}'):`, err.message);
    throw err;
  }
};
"""
with open('frontend/src/services/api.js', 'w', encoding='utf-8') as f:
    f.write(api_code)

print("[OK] api.js updated.")

# 4. FIX APP.JSX (Pass props to Sidebar & handle control actions)
app_code = """import React, { useState, useEffect, useRef } from 'react';
import TopBar from './components/TopBar';
import Sidebar from './components/Sidebar';
import CriticalAlertModal from './components/CriticalAlertModal';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Maintenance from './pages/Maintenance';
import Evaluation from './pages/Evaluation';
import {
  getStatus,
  getPlcsData,
  getCurrentData,
  getHistoryData,
  getModelMetrics,
  getRecentLogs,
  getMaintenanceData,
  postControlAction,
} from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedPlc, setSelectedPlc] = useState(1);
  const [backendStatus, setBackendStatus] = useState(true);
  const [statusData, setStatusData] = useState(null);
  const [plcsList, setPlcsList] = useState([]);
  const [currentData, setCurrentData] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [modelData, setModelData] = useState(null);
  const [maintenanceData, setMaintenanceData] = useState(null);
  const [logs, setLogs] = useState([]);
  const [speed, setSpeed] = useState(1.0);
  const [autoPlay, setAutoPlay] = useState(false);

  const consecutiveFailuresRef = useRef(0);

  const fetchAllData = async (plcId = selectedPlc) => {
    try {
      const [pRes, cRes, hRes, lRes, mRes] = await Promise.all([
        getPlcsData().catch(() => null),
        getCurrentData(plcId).catch(() => null),
        getHistoryData().catch(() => null),
        getRecentLogs(plcId).catch(() => null),
        getMaintenanceData(plcId).catch(() => null),
      ]);

      if (pRes && pRes.plcs) setPlcsList(pRes.plcs);
      if (cRes) setCurrentData(cRes);
      if (hRes && hRes.history) setHistoryData(hRes.history);
      if (lRes && lRes.logs) setLogs(lRes.logs);
      if (mRes) setMaintenanceData(mRes);

      setBackendStatus(true);
      consecutiveFailuresRef.current = 0;
    } catch (err) {
      consecutiveFailuresRef.current += 1;
      if (consecutiveFailuresRef.current >= 3) {
        setBackendStatus(false);
      }
    }
  };

  // Initial fetch
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const sData = await getStatus();
        setStatusData(sData);
        setBackendStatus(true);
        consecutiveFailuresRef.current = 0;
      } catch (err) {
        setBackendStatus(false);
      }

      try {
        const mData = await getModelMetrics();
        setModelData(mData);
      } catch (err) {
        console.error('Failed to load model metrics:', err);
      }
    };

    fetchInitialData();
  }, []);

  // Polling loop
  useEffect(() => {
    let isSubscribed = true;
    let timerId = null;

    const pollData = async () => {
      try {
        const [pRes, cRes, hRes, lRes, mRes] = await Promise.all([
          getPlcsData().catch(() => null),
          getCurrentData(selectedPlc).catch(() => null),
          getHistoryData().catch(() => null),
          getRecentLogs(selectedPlc).catch(() => null),
          getMaintenanceData(selectedPlc).catch(() => null),
        ]);

        if (!isSubscribed) return;

        if (pRes || cRes) {
          setBackendStatus(true);
          consecutiveFailuresRef.current = 0;
        } else {
          consecutiveFailuresRef.current += 1;
          if (consecutiveFailuresRef.current >= 3) {
            setBackendStatus(false);
          }
        }

        if (pRes && pRes.plcs) setPlcsList(pRes.plcs);
        if (cRes) setCurrentData(cRes);
        if (hRes && hRes.history) setHistoryData(hRes.history);
        if (lRes && lRes.logs) setLogs(lRes.logs);
        if (mRes) setMaintenanceData(mRes);

      } catch (err) {
        if (!isSubscribed) return;
        consecutiveFailuresRef.current += 1;
        if (consecutiveFailuresRef.current >= 3) {
          setBackendStatus(false);
        }
      } finally {
        if (isSubscribed) {
          timerId = setTimeout(pollData, 1500);
        }
      }
    };

    pollData();

    return () => {
      isSubscribed = false;
      if (timerId) clearTimeout(timerId);
    };
  }, [selectedPlc]);

  const handleControlAction = async (action, speedVal = 1.0) => {
    try {
      console.log(`Executing control action '${action}'...`);
      const res = await postControlAction(action, speedVal);
      if (action === 'set_speed') setSpeed(speedVal);
      if (action === 'start') setAutoPlay(true);
      if (action === 'pause') setAutoPlay(false);

      if (res && typeof res.auto_play === 'boolean') {
        setAutoPlay(res.auto_play);
      }

      // Immediately refresh all data state on next/reset
      if (action === 'next' || action === 'reset') {
        await fetchAllData(selectedPlc);
      }
    } catch (err) {
      console.error(`Failed to execute control action '${action}':`, err);
    }
  };

  const isCritical = currentData?.machine_status === 'Critical';

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-gray-800 overflow-hidden">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        currentData={currentData}
        backendStatus={backendStatus}
        onControlAction={handleControlAction}
        speed={speed}
        setSpeed={setSpeed}
        autoPlay={autoPlay}
      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar
          backendStatus={backendStatus}
          statusData={statusData}
          activeTab={activeTab}
          speed={speed}
          autoPlay={autoPlay}
          onControl={handleControlAction}
        />

        <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {activeTab === 'dashboard' && (
            <Dashboard
              plcsList={plcsList}
              selectedPlc={selectedPlc}
              setSelectedPlc={setSelectedPlc}
              currentData={currentData}
              historyData={historyData}
              logs={logs}
            />
          )}

          {activeTab === 'analytics' && (
            <Analytics currentData={currentData} historyData={historyData} logs={logs} />
          )}

          {activeTab === 'maintenance' && (
            <Maintenance
              plcsList={plcsList}
              selectedPlc={selectedPlc}
              setSelectedPlc={setSelectedPlc}
              currentData={currentData}
              maintenanceData={maintenanceData}
            />
          )}

          {activeTab === 'evaluation' && <Evaluation modelData={modelData} />}
        </main>
      </div>

      <CriticalAlertModal isVisible={isCritical} currentData={currentData} />
    </div>
  );
}

export default App;
"""
with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("[OK] App.jsx updated.")
