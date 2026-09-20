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

  const fetchAllData = async (plcId = selectedPlc) => {
    try {
      const [pRes, cRes, hRes, lRes, mRes] = await Promise.all([
        getPlcsData().catch(() => null),
        getCurrentData(plcId).catch(() => null),
        getHistoryData(plcId).catch(() => null),
        getRecentLogs(plcId).catch(() => null),
        getMaintenanceData(plcId).catch(() => null),
      ]);

      if (pRes && pRes.plcs) setPlcsList(pRes.plcs);
      if (cRes) setCurrentData(cRes);
      if (hRes) setHistoryData(hRes);
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
          getHistoryData(selectedPlc).catch(() => null),
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
        if (hRes) setHistoryData(hRes);
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
