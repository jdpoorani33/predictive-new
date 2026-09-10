import React, { useState, useEffect, useRef } from 'react';
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

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const sData = await getStatus();
        setStatusData(sData);
        setBackendStatus(true);
        consecutiveFailuresRef.current = 0;
      } catch (err) {}

      try {
        const mData = await getModelMetrics();
        setModelData(mData);
      } catch (err) {
        console.error('Failed to load model metrics:', err);
      }
    };

    fetchInitialData();
  }, []);

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

        if (pRes && pRes.plcs) setPlcsList(pRes.plcs);
        if (cRes) setCurrentData(cRes);
        if (hRes && hRes.history) setHistoryData(hRes.history);
        if (lRes && lRes.logs) setLogs(lRes.logs);
        if (mRes) setMaintenanceData(mRes);

        setBackendStatus(true);
        consecutiveFailuresRef.current = 0;
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
      const res = await postControlAction(action, speedVal);
      if (action === 'set_speed') setSpeed(speedVal);
      if (res && typeof res.auto_play === 'boolean') {
        setAutoPlay(res.auto_play);
      }
    } catch (err) {
      console.error(`Failed to execute control action '${action}':`, err);
    }
  };

  const isCritical = currentData?.machine_status === 'Critical';

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-gray-800 overflow-hidden">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar
          backendStatus={backendStatus}
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
