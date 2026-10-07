import React, { useState } from 'react';
import {
  Thermometer, Activity, Zap, Calendar, ShieldAlert, Gauge, Volume2, ShieldCheck, Cpu,
  Plus, ChevronDown, ChevronUp, Info, HelpCircle, DollarSign, AlertTriangle, CheckCircle, RefreshCw
} from 'lucide-react';
import GaugeCard from '../components/GaugeCard';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import LiveChart from '../components/LiveChart';
import SensorTable from '../components/SensorTable';
import VisualInspectionCard from '../components/VisualInspectionCard';
import { isValidPlcId, formatPlcDisplay, getPlcNumber, isPlcMatch } from '../utils/plcValidation';
import { postAddPlc } from '../services/api';

const Dashboard = ({ plcsList, selectedPlc, setSelectedPlc, selectedTag, setSelectedTag, currentData, historyData, logs, setActiveTab }) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newPlcInput, setNewPlcInput] = useState('');
  const [isSubmittingPlc, setIsSubmittingPlc] = useState(false);
  const [addPlcError, setAddPlcError] = useState(null);
  const [showEvidence, setShowEvidence] = useState(false);

  const health = currentData?.machine_health ?? 100;
  const statusStr = currentData?.machine_status || 'Healthy';
  const conditionStr = currentData?.machine_condition || 'Healthy';
  const anomalyStr = currentData?.anomaly_status || 'Normal';
  const failureRisk = currentData?.failure_risk_pct ?? 0.0;
  const confidence = currentData?.prediction_confidence ?? 95.0;

  const mainIssue = currentData?.main_issue || 'Normal Operation';
  const humanAlert = currentData?.human_readable_alert || '';
  const whyEvidence = currentData?.why_recommendation || [];
  const potentialSavings = currentData?.potential_savings ?? 0;
  const energyIneffPct = currentData?.energy_inefficiency_pct ?? 0;
  const extraEnergyCost = currentData?.additional_energy_cost_per_day ?? 0;

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

  const displayPlcs = validPlcsList.length > 0 ? validPlcsList : [1, 2, 3, 4, 5].map((id) => ({
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

  const handleAddPlcSubmit = async (e) => {
    e.preventDefault();
    if (!newPlcInput.trim()) return;
    setIsSubmittingPlc(true);
    setAddPlcError(null);
    try {
      const res = await postAddPlc(newPlcInput.trim());
      if (res && res.plc_id) {
        setSelectedPlc(res.plc_id);
        setIsAddModalOpen(false);
        setNewPlcInput('');
      }
    } catch (err) {
      setAddPlcError(err?.response?.data?.detail || 'Failed to add PLC. Check identifier format.');
    } finally {
      setIsSubmittingPlc(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Dynamic Multi-PLC and Tag Selector Toolbar with + Add PLC Support */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">Select PLC:</span>
            <select
              value={formatPlcDisplay(selectedPlc)}
              onChange={(e) => setSelectedPlc(e.target.value)}
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
            </select>

            <button
              onClick={() => setIsAddModalOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-3 py-2 rounded-lg flex items-center space-x-1 shadow-sm transition-colors"
              title="Add a new PLC controller unit"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add PLC</span>
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">Select Tag:</span>
            <select
              value={selectedTag || 'Motor_Temp'}
              onChange={(e) => setSelectedTag && setSelectedTag(e.target.value)}
              className="bg-gray-50 border border-gray-300 text-gray-900 text-xs font-bold rounded-lg focus:ring-blue-500 focus:border-blue-500 px-3 py-2 cursor-pointer shadow-sm"
            >
              <option value="Motor_Temp">Motor_Temp (Temperature °C)</option>
              <option value="Vibration_X">Vibration_X (Vibration RMS mm/s)</option>
              <option value="Motor_Current">Motor_Current (Motor Current A)</option>
              <option value="Pressure_Inlet">Pressure_Inlet (Inlet Pressure bar)</option>
              <option value="Noise">Noise (Acoustic Noise dB)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-blue-50 text-blue-800 px-3 py-1.5 rounded-lg border border-blue-200 text-xs font-semibold">
          <span>Active Stream:</span>
          <span className="font-mono font-bold bg-blue-600 text-white px-2 py-0.5 rounded text-[11px]">
            {formatPlcDisplay(selectedPlc)} + {selectedTag || 'Motor_Temp'}
          </span>
        </div>
      </div>

      {/* HUMAN-READABLE PREDICTIVE MAINTENANCE ALERT BANNER */}
      <div className="bg-slate-900 text-white rounded-xl p-4 shadow-md border border-slate-800 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 text-xs font-extrabold bg-blue-600 text-white rounded tracking-wide uppercase">
              PREDICTIVE ALERT SUMMARY
            </span>
            <span className="text-xs font-bold text-slate-300">{formatPlcDisplay(selectedPlc)}</span>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            {potentialSavings > 0 && (
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-0.5 rounded font-mono font-semibold">
                Est. Saving: ₹{potentialSavings.toLocaleString()}
              </span>
            )}
            {energyIneffPct > 0 && (
              <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2.5 py-0.5 rounded font-mono font-semibold">
                Energy: +{energyIneffPct}% (₹{extraEnergyCost.toFixed(0)}/day)
              </span>
            )}
            <button
              onClick={() => setShowEvidence(!showEvidence)}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center space-x-1 font-semibold focus:outline-none"
            >
              <span>Why this recommendation?</span>
              {showEvidence ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        <p className="text-sm font-mono text-slate-100 whitespace-pre-line leading-relaxed">
          {humanAlert || `${formatPlcDisplay(selectedPlc)} — ${mainIssue}.\nRemaining Useful Life: ${currentData?.predicted_rul_days ?? 200} Days. Action: ${currentData?.Recommended_Action || 'Continue Normal Operation'}.`}
        </p>

        {showEvidence && (
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-700 space-y-2 text-xs">
            <div className="font-bold text-blue-300 flex items-center space-x-1.5">
              <HelpCircle className="w-4 h-4 text-blue-400" />
              <span>Model & Sensor Evidence Analysis</span>
            </div>
            {whyEvidence && whyEvidence.length > 0 ? (
              <ul className="space-y-1 text-slate-300 font-mono">
                {whyEvidence.map((bullet, idx) => (
                  <li key={idx} className="flex items-start space-x-1.5">
                    <span className="text-blue-400 font-bold">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-400">All sensor telemetry, FFT spectral frequencies, and model outputs are operating within normal baseline limits.</p>
            )}
          </div>
        )}
      </div>

      {/* MULTI-MACHINE REAL-TIME OVERVIEW GRID */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-gray-900">Multi-PLC Industrial Digital Twin Overview</h2>
          </div>
          <span className="text-xs font-semibold text-gray-500 bg-gray-100 px-2.5 py-1 rounded border">
            Topic: plc/# | Broker: broker.hivemq.com:1883
          </span>
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

      {/* SYSTEM STATE SUMMARY FOR SELECTED PLC */}
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
          title="Motor Temperature"
          value={currentData?.temperature ?? '--'}
          unit="°C"
          icon={Thermometer}
          valueColor="text-amber-600"
        />

        <MetricCard
          title="Vibration RMS"
          value={currentData?.vibration ?? '--'}
          unit="mm/s"
          icon={Activity}
          valueColor="text-emerald-600"
        />

        <MetricCard
          title="Motor Current"
          value={currentData?.motor_current ?? '--'}
          unit="A"
          icon={Zap}
          valueColor="text-indigo-600"
        />

        <MetricCard
          title="Inlet Pressure"
          value={currentData?.pressure ?? '--'}
          unit="bar"
          icon={Gauge}
          valueColor="text-cyan-600"
        />

        <MetricCard
          title="Acoustic Noise"
          value={currentData?.noise ?? '--'}
          unit="dB"
          icon={Volume2}
          valueColor="text-violet-600"
        />
      </div>

      {/* Row 2: Live Real-Time Telemetry Trend Chart */}
      <LiveChart
        historyData={historyData}
        selectedTag={selectedTag || 'Motor_Temp'}
        selectedPlc={formatPlcDisplay(selectedPlc)}
      />

      {/* Row 3: YOLO11 Visual Health & Gold Reference Inspection Module */}
      <VisualInspectionCard selectedPlc={formatPlcDisplay(selectedPlc)} setActiveTab={setActiveTab} />

      {/* Row 4: Historical Log & Recent Observations Table */}
      <SensorTable logs={logs} selectedPlc={formatPlcDisplay(selectedPlc)} />

      {/* ADD PLC MODAL */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl border border-gray-200 space-y-4 animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-base font-bold text-gray-900 flex items-center space-x-2">
                <Plus className="w-5 h-5 text-blue-600" />
                <span>Register Additional PLC Machine</span>
              </h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-gray-400 hover:text-gray-600 text-lg font-bold">×</button>
            </div>

            <form onSubmit={handleAddPlcSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">PLC Identifier (e.g. PLC_06, PLC6, 6):</label>
                <input
                  type="text"
                  required
                  placeholder="PLC_06"
                  value={newPlcInput}
                  onChange={(e) => setNewPlcInput(e.target.value)}
                  className="w-full bg-gray-50 border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              {addPlcError && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 font-semibold">
                  {addPlcError}
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingPlc}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow transition-colors flex items-center space-x-1.5"
                >
                  {isSubmittingPlc ? <RefreshCw className="w-4 h-4 animate-spin" /> : <span>Add PLC</span>}
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
