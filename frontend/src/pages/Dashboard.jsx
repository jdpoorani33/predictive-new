import React from 'react';
import { Thermometer, Activity, Zap, Calendar, ShieldAlert, Gauge, Volume2, ShieldCheck, Cpu } from 'lucide-react';
import GaugeCard from '../components/GaugeCard';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import LiveChart from '../components/LiveChart';
import SensorTable from '../components/SensorTable';

const Dashboard = ({ plcsList, selectedPlc, setSelectedPlc, currentData, historyData, logs }) => {
  const health = currentData?.machine_health ?? 100;
  const statusStr = currentData?.machine_status || 'Healthy';
  const conditionStr = currentData?.machine_condition || 'Healthy';
  const anomalyStr = currentData?.anomaly_status || 'Normal';
  const failureRisk = currentData?.failure_risk_pct ?? 0.0;
  const confidence = currentData?.prediction_confidence ?? 95.0;

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
    switch (id) {
      case 1: return 'Healthy Baseline';
      case 2: return 'High Operating Load';
      case 3: return 'Bearing Degradation';
      case 4: return 'Elevated Thermal Stress';
      case 5: return 'Normal Variation';
      default: return `PLC Machine #${id}`;
    }
  };

  // Fallback 5 PLCs list if backend list loading
  const displayPlcs = plcsList && plcsList.length > 0 ? plcsList : [1,2,3,4,5].map(id => ({
    plc_id: id,
    temperature: currentData?.plc_id === id ? currentData.temperature : 62.0,
    vibration: currentData?.plc_id === id ? currentData.vibration : 0.2,
    motor_current: currentData?.plc_id === id ? currentData.motor_current : 8.0,
    pressure: currentData?.plc_id === id ? currentData.pressure : 5.0,
    noise: currentData?.plc_id === id ? currentData.noise : 42.0,
    predicted_rul_days: currentData?.plc_id === id ? currentData.predicted_rul_days : 200,
    machine_status: currentData?.plc_id === id ? currentData.machine_status : 'Healthy',
    anomaly_status: currentData?.plc_id === id ? currentData.anomaly_status : 'Normal',
  }));

  return (
    <div className="space-y-5">
      {/* 5-PLC MULTI-MACHINE REAL-TIME OVERVIEW GRID (Person 3 Dashboard Requirement) */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-gray-900">5-PLC Industrial MQTT Digital Twin Overview</h2>
          </div>
          <span className="text-xs font-semibold text-gray-500 bg-gray-100 px-2.5 py-1 rounded border">
            Topic: plc/# | Broker: broker.hivemq.com:1883
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {displayPlcs.map((p) => {
            const isSelected = p.plc_id === selectedPlc;
            const pStatus = p.machine_status || 'Healthy';
            const pRul = p.predicted_rul_days ?? '--';
            const pAnomaly = p.anomaly_status === 'Anomaly Detected';

            return (
              <div
                key={p.plc_id}
                onClick={() => setSelectedPlc(p.plc_id)}
                className={`cursor-pointer rounded-xl p-3 border transition-all duration-200 ${
                  isSelected
                    ? 'border-indigo-600 bg-indigo-50/40 shadow-md ring-2 ring-indigo-500/20'
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-1.5">
                    <span className={`w-2.5 h-2.5 rounded-full ${isSelected ? 'bg-indigo-600 animate-pulse' : 'bg-gray-400'}`}></span>
                    <span className="font-bold text-sm text-gray-900">PLC {p.plc_id}</span>
                  </div>
                  <StatusBadge status={pStatus} />
                </div>

                <div className="text-[11px] font-semibold text-gray-500 mb-2 truncate">
                  {getPlcDesc(p.plc_id)}
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
            <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">PLC {selectedPlc} Machine Condition</div>
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

      {/* Row 2: Live Sensor Graph */}
      <LiveChart historyData={historyData} />

      {/* Row 3: Recent Sensor Readings Table */}
      <SensorTable logs={logs} />
    </div>
  );
};

export default Dashboard;
