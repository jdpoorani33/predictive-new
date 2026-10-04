import React, { useState, useMemo } from 'react';
import {
  Thermometer,
  Activity,
  Zap,
  Calendar,
  ShieldAlert,
  Gauge,
  Volume2,
  ShieldCheck,
  Cpu,
  PlusCircle,
  Plus,
  X,
  AlertCircle
} from 'lucide-react';
import GaugeCard from '../components/GaugeCard';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import LiveChart from '../components/LiveChart';
import SensorTable from '../components/SensorTable';
import { isValidPlcId, formatPlcDisplay, getPlcNumber, isPlcMatch } from '../utils/plcValidation';
import { addPlcApi } from '../services/api';

const Dashboard = ({
  plcsList,
  selectedPlc,
  setSelectedPlc,
  selectedTag,
  setSelectedTag,
  currentData,
  historyData,
  logs,
  onAddPlcSuccess
}) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [newPlcName, setNewPlcName] = useState('PLC_06');
  const [plcInputError, setPlcInputError] = useState('');
  const [isSubmittingPlc, setIsSubmittingPlc] = useState(false);

  const health = currentData?.machine_health ?? 100;
  const statusStr = currentData?.machine_status || 'Healthy';
  const conditionStr = currentData?.machine_condition || 'Healthy';
  const anomalyStr = currentData?.anomaly_status || 'Normal';
  const failureRisk = currentData?.failure_risk_pct ?? 0.0;
  const confidence = currentData?.prediction_confidence ?? 95.0;

  const isPlcSelected = (pId) => {
    if (!isValidPlcId(pId) || !isValidPlcId(selectedPlc)) return false;
    return isPlcMatch(pId, selectedPlc);
  };

  const getGaugeColor = (s) => {
    switch (s) {
      case 'Healthy':
        return '#22C55E';
      case 'Slight Wear':
        return '#2563EB';
      case 'Moderate Wear':
        return '#F59E0B';
      case 'Warning':
        return '#D97706';
      case 'Critical':
        return '#EF4444';
      default:
        return '#22C55E';
    }
  };

  const statusColor = getGaugeColor(statusStr);

  const getPlcDesc = (id) => {
    const num = typeof id === 'number' && !isNaN(id) ? id : 1;
    switch (num) {
      case 1: return 'Healthy Baseline Unit';
      case 2: return 'High Operating Load';
      case 3: return 'Bearing Degradation Unit';
      case 4: return 'Elevated Thermal Stress';
      case 5: return 'Normal Variation';
      default: return `Turbine Motor Unit #${num}`;
    }
  };

  // Filter plcsList strictly to only valid PLC IDs
  const validPlcsList = (plcsList || [])
    .filter((p) => p && isValidPlcId(p.plc_id))
    .map((p) => ({
      ...p,
      plc_id: formatPlcDisplay(p.plc_id),
      plc_id_num: getPlcNumber(p.plc_id),
    }));

  // Fallback 5 PLCs list if backend list loading
  const basePlcs = [1, 2, 3, 4, 5].map((id) => ({
    plc_id: `PLC_${String(id).padStart(2, '0')}`,
    plc_id_num: id,
    temperature: currentData?.plc_id === id ? currentData.temperature : 62.0,
    vibration: currentData?.plc_id === id ? currentData.vibration : 0.2,
    motor_current: currentData?.plc_id === id ? currentData.motor_current : 8.0,
    pressure: currentData?.plc_id === id ? currentData.pressure : 5.0,
    noise: currentData?.plc_id === id ? currentData.noise : 42.0,
    predicted_rul_days: currentData?.plc_id === id ? currentData.predicted_rul_days : 200,
    machine_status: currentData?.plc_id === id ? currentData.machine_status : 'Healthy',
    anomaly_status: currentData?.plc_id === id ? currentData.anomaly_status : 'Normal',
  }));

  // Combine base PLCs with any dynamically added PLCs
  const displayPlcs = useMemo(() => {
    const combined = [...basePlcs];
    validPlcsList.forEach((vp) => {
      if (!combined.some((b) => isPlcMatch(b.plc_id, vp.plc_id))) {
        combined.push(vp);
      }
    });
    return combined.sort((a, b) => (a.plc_id_num || 0) - (b.plc_id_num || 0));
  }, [validPlcsList, currentData]);

  // Dynamic Sensor Dropdown List (Requirement 3: MQTT dynamic identification)
  const sensorOptions = useMemo(() => {
    const baseSensors = [
      { value: 'Motor_Temp', label: 'Motor_Temp (Temperature °C)' },
      { value: 'Vibration_X', label: 'Vibration (Vibration RMS mm/s)' },
      { value: 'Motor_Current', label: 'Motor_Current (Motor Current A)' },
      { value: 'Pressure_Inlet', label: 'Pressure (Inlet Pressure bar)' },
      { value: 'Noise', label: 'Noise (Acoustic Noise dB)' }
    ];

    const discoveredKeys = new Set(baseSensors.map(s => s.value));

    // Inspect currentData tags object
    if (currentData) {
      if (currentData.tags && typeof currentData.tags === 'object') {
        Object.keys(currentData.tags).forEach(k => discoveredKeys.add(k));
      }
      Object.keys(currentData).forEach(k => {
        if (!['plc_id', 'plc_id_num', 'timestamp', 'machine_health', 'machine_status', 'machine_condition', 'anomaly_status', 'failure_risk_pct', 'prediction_confidence', 'model_used', 'predicted_rul_days', 'actual_rul_days'].includes(k)) {
          if (typeof currentData[k] === 'number') {
            discoveredKeys.add(k);
          }
        }
      });
    }

    const optionsList = Array.from(discoveredKeys).map(k => {
      const match = baseSensors.find(bs => bs.value === k || bs.value.toLowerCase() === k.toLowerCase());
      if (match) return match;
      return { value: k, label: `${k} (MQTT Sensor)` };
    });

    return optionsList;
  }, [currentData]);

  // Handle Add PLC Form Submit
  const handleAddPlcSubmit = async (e) => {
    e.preventDefault();
    setPlcInputError('');

    const trimmed = newPlcName.trim();
    if (!trimmed) {
      setPlcInputError('PLC Name cannot be empty.');
      return;
    }

    if (!isValidPlcId(trimmed)) {
      setPlcInputError('Invalid PLC Name format. Example: PLC_06 or PLC6');
      return;
    }

    const normName = formatPlcDisplay(trimmed);

    // Check for duplicate PLC ID
    if (displayPlcs.some((p) => isPlcMatch(p.plc_id, normName))) {
      setPlcInputError(`PLC "${normName}" already exists.`);
      return;
    }

    try {
      setIsSubmittingPlc(true);
      await addPlcApi(normName);

      if (onAddPlcSuccess) {
        onAddPlcSuccess(normName);
      } else {
        setSelectedPlc(normName);
      }

      setShowAddModal(false);
      setNewPlcName('PLC_07');
    } catch (err) {
      console.error('Failed to add PLC:', err);
      // Even if API fails due to network, support local session addition
      if (onAddPlcSuccess) {
        onAddPlcSuccess(normName);
      } else {
        setSelectedPlc(normName);
      }
      setShowAddModal(false);
    } finally {
      setIsSubmittingPlc(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* PLC & Sensor Selection Toolbar */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* PLC Dropdown */}
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">Select PLC:</span>
            <select
              value={formatPlcDisplay(selectedPlc)}
              onChange={(e) => {
                if (e.target.value === 'ADD_NEW_PLC') {
                  setShowAddModal(true);
                } else {
                  setSelectedPlc(e.target.value);
                }
              }}
              className="bg-gray-50 border border-gray-300 text-gray-900 text-xs font-bold rounded-lg focus:ring-blue-500 focus:border-blue-500 px-3 py-2 cursor-pointer shadow-sm"
            >
              {displayPlcs
                .filter((p) => p && isValidPlcId(p.plc_id))
                .map((p) => {
                  const pKey = formatPlcDisplay(p.plc_id);
                  const pNum = getPlcNumber(pKey);
                  return (
                    <option key={pKey} value={pKey}>
                      {pKey} — {getPlcDesc(pNum)}
                    </option>
                  );
                })}
              <option value="ADD_NEW_PLC" className="font-bold text-blue-600 bg-blue-50">
                + Add PLC
              </option>
            </select>
          </div>

          {/* Dynamic Sensor Dropdown */}
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">Select Sensor:</span>
            <select
              value={selectedTag || 'Motor_Temp'}
              onChange={(e) => setSelectedTag && setSelectedTag(e.target.value)}
              className="bg-gray-50 border border-gray-300 text-gray-900 text-xs font-bold rounded-lg focus:ring-blue-500 focus:border-blue-500 px-3 py-2 cursor-pointer shadow-sm"
            >
              {sensorOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-blue-50 text-blue-800 px-3 py-1.5 rounded-lg border border-blue-200 text-xs font-semibold">
          <span>Active Stream:</span>
          <span className="font-mono font-bold bg-blue-600 text-white px-2 py-0.5 rounded text-[11px]">
            {formatPlcDisplay(selectedPlc)} → {selectedTag || 'Motor_Temp'}
          </span>
        </div>
      </div>

      {/* MULTI-MACHINE REAL-TIME OVERVIEW GRID */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-gray-900">Industrial Machine Overview</h2>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center space-x-1 text-xs font-bold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg border border-blue-200 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Add PLC</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {displayPlcs
            .filter((p) => p && isValidPlcId(p.plc_id))
            .map((p) => {
              const pKey = formatPlcDisplay(p.plc_id);
              const isSelected = isPlcSelected(pKey);
              const pStatus = p.machine_status || 'Healthy';
              const pRul = p.predicted_rul_days ?? '--';
              const pAnomaly = p.anomaly_status === 'Anomaly Detected';
              const pNum = getPlcNumber(pKey);

              return (
                <div
                  key={pKey}
                  onClick={() => setSelectedPlc(pKey)}
                  className={`cursor-pointer rounded-xl p-3 border transition-all duration-200 ${
                    isSelected
                      ? 'border-indigo-600 bg-indigo-50/40 shadow-md ring-2 ring-indigo-500/20'
                      : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center space-x-1.5">
                      <span className={`w-2.5 h-2.5 rounded-full ${isSelected ? 'bg-indigo-600 animate-pulse' : 'bg-gray-400'}`}></span>
                      <span className="font-bold text-sm text-gray-900">{pKey}</span>
                    </div>
                    <StatusBadge status={pStatus} />
                  </div>

                  <div className="text-[11px] font-semibold text-gray-500 mb-2 truncate">
                    {getPlcDesc(pNum)}
                  </div>

                  <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-xs text-gray-600 border-t border-b border-gray-100 py-1.5 mb-2">
                    <div>Temp: <span className="font-bold text-gray-900">{p.temperature ?? '--'}°C</span></div>
                    <div>Vib: <span className="font-bold text-gray-900">{p.vibration ?? '--'}</span></div>
                    <div>Curr: <span className="font-bold text-gray-900">{p.motor_current ?? '--'}A</span></div>
                    <div>Press: <span className="font-bold text-gray-900">{p.pressure ?? '--'}</span></div>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <div>
                      <span className="text-gray-400 text-[10px] block">RF RUL</span>
                      <span className="font-bold font-mono text-indigo-700">{pRul} Days</span>
                    </div>
                    <div className="text-right">
                      <span className="text-gray-400 text-[10px] block">Anomaly</span>
                      <span className={`font-semibold ${pAnomaly ? 'text-red-600' : 'text-emerald-600'}`}>
                        {pAnomaly ? '⚠️ Anomaly' : '✓ Normal'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Top Banner / System State Summary for Selected PLC */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${conditionStr === 'Critical' ? 'bg-red-100 text-red-700' : conditionStr === 'Warning' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">{formatPlcDisplay(selectedPlc)} Machine Condition</div>
            <div className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <span>{conditionStr}</span>
              <span className="text-gray-300">•</span>
              <span className={`text-xs font-semibold ${anomalyStr === 'Anomaly Detected' ? 'text-red-600 font-bold' : 'text-emerald-600'}`}>
                {anomalyStr === 'Anomaly Detected' ? '⚠️ Anomaly Detected (Isolation Forest)' : '✓ Normal Operation'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-6">
          <div>
            <span className="text-xs text-gray-500 block">Failure Risk</span>
            <span className={`text-base font-bold font-mono ${failureRisk > 50 ? 'text-red-600' : failureRisk > 25 ? 'text-amber-600' : 'text-emerald-600'}`}>
              {failureRisk.toFixed(1)}%
            </span>
          </div>

          <div>
            <span className="text-xs text-gray-500 block">RUL Confidence</span>
            <span className="text-base font-bold font-mono text-blue-600">
              {confidence.toFixed(1)}%
            </span>
          </div>

          <div>
            <span className="text-xs text-gray-500 block">Active ML Model</span>
            <span className="text-xs font-bold text-gray-800 bg-gray-100 px-2.5 py-1 rounded border border-gray-200 block">
              {currentData?.model_used || 'Random Forest Regressor'}
            </span>
          </div>
        </div>
      </div>

      {/* Row 1: Health Gauge and 5 Sensor + RUL Metric Cards for Selected PLC */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 items-stretch">
        <div className="lg:col-span-1 min-w-[200px]">
          <GaugeCard value={health} statusColor={statusColor} />
        </div>

        <MetricCard
          title="Remaining Useful Life"
          value={currentData?.predicted_rul_days ?? '--'}
          unit="Days"
          icon={Calendar}
          valueColor="text-blue-600"
        />

        <MetricCard
          title="Machine Stage"
          badgeComponent={<StatusBadge status={currentData?.machine_status || 'Healthy'} />}
        />

        <MetricCard
          title="Temperature"
          value={currentData?.temperature ?? '--'}
          unit="°C"
          icon={Thermometer}
        />

        <MetricCard
          title="Vibration RMS"
          value={currentData?.vibration ?? '--'}
          unit="mm/s"
          icon={Activity}
        />

        <MetricCard
          title="Motor Current"
          value={currentData?.motor_current ?? '--'}
          unit="A"
          icon={Zap}
        />

        <MetricCard
          title="Pressure"
          value={currentData?.pressure ?? '--'}
          unit="bar"
          icon={Gauge}
        />
      </div>

      {/* Row 2: Live Sensor Graph - Real vs Guessed / Predicted on SAME Chart */}
      <LiveChart
        historyData={historyData}
        selectedPlc={selectedPlc}
        setSelectedPlc={setSelectedPlc}
        selectedTag={selectedTag}
        setSelectedTag={setSelectedTag}
        plcsList={displayPlcs}
        onOpenAddModal={() => setShowAddModal(true)}
      />

      {/* Row 3: Recent Sensor Readings Table */}
      <SensorTable logs={logs} />

      {/* ADD NEW PLC MODAL (Requirement 2) */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <PlusCircle className="w-5 h-5 text-blue-600" />
                <span>Add New PLC</span>
              </h3>
              <button
                onClick={() => { setShowAddModal(false); setPlcInputError(''); }}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {plcInputError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs font-semibold rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{plcInputError}</span>
              </div>
            )}

            <form onSubmit={handleAddPlcSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  PLC Name / ID:
                </label>
                <input
                  type="text"
                  value={newPlcName}
                  onChange={(e) => { setNewPlcName(e.target.value); setPlcInputError(''); }}
                  placeholder="e.g. PLC_06"
                  className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm font-mono font-bold rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 p-2.5 outline-none"
                  autoFocus
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  Enter a unique PLC identifier (e.g. PLC_06, PLC_07).
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => { setShowAddModal(false); setPlcInputError(''); }}
                  className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingPlc}
                  className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Plus className="w-4 h-4" />
                  <span>{isSubmittingPlc ? 'Adding...' : 'Add PLC'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
