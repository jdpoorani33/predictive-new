import React, { useState, useEffect, useRef } from 'react';
import {
  Calendar, Wrench, ShieldCheck, Clock, TrendingUp, DollarSign,
  AlertCircle, RefreshCw, Zap, Sliders, CheckCircle, AlertTriangle,
  ChevronDown, ChevronUp, Info, HelpCircle, Activity, Cpu
} from 'lucide-react';
import MetricCard from './MetricCard';
import StatusBadge from './StatusBadge';
import Plot from 'react-plotly.js';
import { calculateAdaptiveYRange } from './LiveChart';
import {
  getMaintenanceOverview,
  getEnergyData,
  getCostConfig,
  postCostConfig,
  getMaintenanceHistoryData
} from '../services/api';

const MaintenanceCostPlot = ({ costChartData = [] }) => {
  if (!costChartData || costChartData.length === 0) {
    return (
      <div className="industrial-card p-6 w-full h-64 flex flex-col items-center justify-center space-y-2 bg-gray-50 border border-gray-200 rounded-xl">
        <Clock className="w-8 h-8 text-gray-400" />
        <span className="text-xs font-bold text-gray-600">No maintenance cost data available.</span>
      </div>
    );
  }

  const plcs = costChartData.map((d) => d.plc_id);
  const preventiveCosts = costChartData.map((d) => d.preventive_cost);
  const failureCosts = costChartData.map((d) => d.expected_failure_cost);

  return (
    <div className="industrial-card p-5 w-full bg-white rounded-xl border border-gray-200 shadow-sm space-y-3">
      <div className="flex items-center justify-between border-b border-gray-100 pb-3">
        <div>
          <h3 className="text-sm font-bold text-gray-900 flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-emerald-600" />
            <span>Preventive Maintenance Cost vs Expected Failure Cost (Per PLC)</span>
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Financial cost-benefit comparison: Highlights where preventive servicing yields maximum cost savings over waiting for failure.
          </p>
        </div>
        <span className="px-2.5 py-1 text-xs font-bold bg-blue-50 text-blue-800 border border-blue-200 rounded-lg">
          Live Financial Optimization
        </span>
      </div>

      <div className="w-full h-72">
        <Plot
          data={[
            {
              x: plcs,
              y: preventiveCosts,
              name: 'Preventive Servicing Cost (₹)',
              type: 'bar',
              marker: { color: '#2563EB' },
              hovertemplate: `Preventive Cost: ₹%{y:,.0f}<extra></extra>`
            },
            {
              x: plcs,
              y: failureCosts,
              name: 'Expected Failure Cost (₹)',
              type: 'bar',
              marker: { color: '#EF4444' },
              hovertemplate: `Expected Failure Cost: ₹%{y:,.0f}<extra></extra>`
            }
          ]}
          layout={{
            barmode: 'group',
            autosize: true,
            height: 270,
            margin: { l: 55, r: 20, t: 15, b: 40 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: '#FAFAFA',
            xaxis: {
              title: { text: 'Machine PLC Identifier', font: { size: 10, color: '#6B7280' } },
              gridcolor: '#E5E7EB',
              zeroline: false
            },
            yaxis: {
              title: { text: 'Cost (₹ INR)', font: { size: 10, color: '#6B7280' } },
              gridcolor: '#E5E7EB',
              zeroline: false
            },
            legend: {
              orientation: 'h',
              y: 1.15,
              x: 1,
              xanchor: 'right',
              font: { size: 10, color: '#374151' }
            }
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
          config={{ displayModeBar: false, responsive: true }}
        />
      </div>
    </div>
  );
};


const EnergyMonitoringPlot = ({ energyData, selectedPlc, setSelectedPlc, plcsList = [] }) => {
  const trend = energyData?.trend || {};
  const timestamps = trend.timestamps || [];
  const baseline = trend.baseline_kwh || [];
  const current = trend.current_kwh || [];
  const excess = trend.excess_kwh || [];

  const ineffPct = energyData?.energy_inefficiency_pct ?? 0.0;
  const extraCost = energyData?.additional_energy_cost_per_day ?? 0.0;

  return (
    <div className="industrial-card p-5 w-full bg-white rounded-xl border border-gray-200 shadow-sm space-y-3">
      <div className="flex flex-wrap items-center justify-between border-b border-gray-100 pb-3 gap-2">
        <div>
          <h3 className="text-sm font-bold text-gray-900 flex items-center space-x-2">
            <Zap className="w-4 h-4 text-amber-500" />
            <span>Energy-Aware Telemetry & Baseline Consumption Trend</span>
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Monitors 3-Phase Electrical Power & Energy degradation relative to normal baseline for {selectedPlc}.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold text-gray-600">Target PLC:</span>
          <select
            value={selectedPlc}
            onChange={(e) => setSelectedPlc(e.target.value)}
            className="bg-gray-50 border border-gray-300 text-gray-900 text-xs font-bold rounded-lg px-2.5 py-1 cursor-pointer"
          >
            {plcsList.map((p) => (
              <option key={p.plc_id} value={p.plc_id}>
                {p.plc_id}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-amber-50/50 p-3 rounded-lg border border-amber-100 text-xs">
        <div>
          <span className="text-gray-500 block">Baseline Energy</span>
          <span className="font-bold font-mono text-gray-800">{energyData?.baseline_energy_kwh ?? '--'} kWh/day</span>
        </div>
        <div>
          <span className="text-gray-500 block">Current Energy</span>
          <span className="font-bold font-mono text-amber-700">{energyData?.current_energy_kwh ?? '--'} kWh/day</span>
        </div>
        <div>
          <span className="text-gray-500 block">Energy Inefficiency</span>
          <span className={`font-bold font-mono ${ineffPct > 10 ? 'text-red-600' : 'text-emerald-600'}`}>
            +{ineffPct}% above baseline
          </span>
        </div>
        <div>
          <span className="text-gray-500 block">Additional Cost</span>
          <span className="font-bold font-mono text-rose-700">₹{extraCost.toFixed(0)} / day</span>
        </div>
      </div>

      <div className="w-full h-64">
        <Plot
          data={[
            {
              x: timestamps.map((_, i) => `Step ${i + 1}`),
              y: baseline,
              name: 'Normal Baseline (kWh/day)',
              type: 'scatter',
              mode: 'lines',
              line: { color: '#10B981', width: 2, dash: 'dash' },
              hovertemplate: `Baseline: %{y:.1f} kWh/day<extra></extra>`
            },
            {
              x: timestamps.map((_, i) => `Step ${i + 1}`),
              y: current,
              name: 'Current Consumption (kWh/day)',
              type: 'scatter',
              mode: 'lines+markers',
              line: { color: '#F59E0B', width: 3 },
              marker: { size: 4, color: '#F59E0B' },
              hovertemplate: `Current: %{y:.1f} kWh/day<extra></extra>`
            },
            {
              x: timestamps.map((_, i) => `Step ${i + 1}`),
              y: excess,
              name: 'Excess Consumption (kWh/day)',
              type: 'bar',
              marker: { color: 'rgba(239, 68, 68, 0.4)' },
              hovertemplate: `Excess: %{y:.1f} kWh/day<extra></extra>`
            }
          ]}
          layout={{
            autosize: true,
            height: 240,
            margin: { l: 50, r: 15, t: 15, b: 35 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: '#FAFAFA',
            xaxis: {
              title: { text: 'Telemetry Timeline', font: { size: 10, color: '#6B7280' } },
              gridcolor: '#E5E7EB',
              zeroline: false
            },
            yaxis: {
              title: { text: 'Energy (kWh/day)', font: { size: 10, color: '#6B7280' } },
              gridcolor: '#E5E7EB',
              zeroline: false
            },
            legend: {
              orientation: 'h',
              y: 1.15,
              x: 1,
              xanchor: 'right',
              font: { size: 10, color: '#374151' }
            }
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
          config={{ displayModeBar: false, responsive: true }}
        />
      </div>
    </div>
  );
};


const CostConfigDrawer = ({ costConfig, onSaveConfig }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    labour_cost: costConfig?.labour_cost ?? 3000,
    spare_parts_cost: costConfig?.spare_parts_cost ?? 3500,
    inspection_cost: costConfig?.inspection_cost ?? 1000,
    service_cost: costConfig?.service_cost ?? 500,
    repair_replacement_cost: costConfig?.repair_replacement_cost ?? 12000,
    downtime_cost: costConfig?.downtime_cost ?? 8000,
    production_loss: costConfig?.production_loss ?? 4000,
    emergency_labour_cost: costConfig?.emergency_labour_cost ?? 6000,
    electricity_rate: costConfig?.electricity_rate ?? 8.0,
  });

  useEffect(() => {
    if (costConfig) {
      setFormData({
        labour_cost: costConfig.labour_cost ?? 3000,
        spare_parts_cost: costConfig.spare_parts_cost ?? 3500,
        inspection_cost: costConfig.inspection_cost ?? 1000,
        service_cost: costConfig.service_cost ?? 500,
        repair_replacement_cost: costConfig.repair_replacement_cost ?? 12000,
        downtime_cost: costConfig.downtime_cost ?? 8000,
        production_loss: costConfig.production_loss ?? 4000,
        emergency_labour_cost: costConfig.emergency_labour_cost ?? 6000,
        electricity_rate: costConfig.electricity_rate ?? 8.0,
      });
    }
  }, [costConfig]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: parseFloat(value) || 0 }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSaveConfig(formData);
  };

  return (
    <div className="industrial-card bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-xs font-bold text-gray-800 uppercase tracking-wider focus:outline-none"
      >
        <div className="flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-blue-600" />
          <span>Interactive Maintenance Cost & Energy Parameter Configuration</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-[11px] text-gray-500 font-normal">
            {isOpen ? 'Collapse Controls' : 'Edit Cost & Energy Assumptions'}
          </span>
          {isOpen ? <ChevronUp className="w-4 h-4 text-gray-600" /> : <ChevronDown className="w-4 h-4 text-gray-600" />}
        </div>
      </button>

      {isOpen && (
        <form onSubmit={handleSubmit} className="mt-4 border-t border-gray-100 pt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {/* Preventive Cost Components */}
            <div className="bg-blue-50/50 p-3 rounded-lg border border-blue-100 space-y-2">
              <h4 className="font-bold text-blue-900 border-b border-blue-200 pb-1">Preventive Servicing Costs (₹)</h4>
              <div>
                <label className="text-gray-600 block mb-0.5">Labour Cost (₹):</label>
                <input type="number" name="labour_cost" value={formData.labour_cost} onChange={handleChange} className="w-full bg-white border rounded px-2 py-1" />
              </div>
              <div>
                <label className="text-gray-600 block mb-0.5">Spare Parts Cost (₹):</label>
                <input type="number" name="spare_parts_cost" value={formData.spare_parts_cost} onChange={handleChange} className="w-full bg-white border rounded px-2 py-1" />
              </div>
              <div>
                <label className="text-gray-600 block mb-0.5">Inspection Cost (₹):</label>
                <input type="number" name="inspection_cost" value={formData.inspection_cost} onChange={handleChange} className="w-full bg-white border rounded px-2 py-1" />
              </div>
              <div>
                <label className="text-gray-600 block mb-0.5">Service Cost (₹):</label>
                <input type="number" name="service_cost" value={formData.service_cost} onChange={handleChange} className="w-full bg-white border rounded px-2 py-1" />
              </div>
            </div>

            {/* Failure Impact Components */}
            <div className="bg-rose-50/50 p-3 rounded-lg border border-rose-100 space-y-2">
              <h4 className="font-bold text-rose-900 border-b border-rose-200 pb-1">Breakdown Failure Impact (₹)</h4>
              <div>
                <label className="text-gray-600 block mb-0.5">Emergency Repair / Replacement (₹):</label>
                <input type="number" name="repair_replacement_cost" value={formData.repair_replacement_cost} onChange={handleChange} className="w-full bg-white border rounded px-2 py-1" />
              </div>
              <div>
                <label className="text-gray-600 block mb-0.5">Downtime Loss (₹):</label>
                <input type="number" name="downtime_cost" value={formData.downtime_cost} onChange={handleChange} className="w-full bg-white border rounded px-2 py-1" />
              </div>
              <div>
                <label className="text-gray-600 block mb-0.5">Production Output Loss (₹):</label>
                <input type="number" name="production_loss" value={formData.production_loss} onChange={handleChange} className="w-full bg-white border rounded px-2 py-1" />
              </div>
              <div>
                <label className="text-gray-600 block mb-0.5">Emergency Labour Overtime (₹):</label>
                <input type="number" name="emergency_labour_cost" value={formData.emergency_labour_cost} onChange={handleChange} className="w-full bg-white border rounded px-2 py-1" />
              </div>
            </div>

            {/* Electricity Rate & Energy Parameters */}
            <div className="bg-amber-50/50 p-3 rounded-lg border border-amber-100 space-y-2">
              <h4 className="font-bold text-amber-900 border-b border-amber-200 pb-1">Energy Rate & Grid Assumptions</h4>
              <div>
                <label className="text-gray-600 block mb-0.5">Electricity Tariff Rate (₹ / kWh):</label>
                <input type="number" step="0.5" name="electricity_rate" value={formData.electricity_rate} onChange={handleChange} className="w-full bg-white border rounded px-2 py-1" />
              </div>
              <p className="text-[11px] text-gray-500 pt-2">
                Updating these parameters recalculates expected breakdown loss, net cost savings, and excess energy costs dynamically across all PLCs.
              </p>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-4 py-2 rounded-lg shadow transition-colors"
            >
              Apply Cost Parameters
            </button>
          </div>
        </form>
      )}
    </div>
  );
};


const MaintenanceDashboard = ({ maintenanceData, historyData, selectedPlc = 'PLC_01' }) => {
  const [overview, setOverview] = useState(null);
  const [energyInfo, setEnergyInfo] = useState(null);
  const [currentSelectedPlc, setCurrentSelectedPlc] = useState(selectedPlc);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setCurrentSelectedPlc(selectedPlc);
  }, [selectedPlc]);

  const loadOverviewData = async () => {
    try {
      const [ovData, enData] = await Promise.all([
        getMaintenanceOverview().catch(() => null),
        getEnergyData(currentSelectedPlc).catch(() => null)
      ]);
      if (ovData) setOverview(ovData);
      if (enData) setEnergyInfo(enData);
    } catch (err) {
      console.error('Failed to load maintenance overview:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOverviewData();
  }, [currentSelectedPlc]);

  const handleSaveCostConfig = async (newConfig) => {
    try {
      await postCostConfig(newConfig);
      await loadOverviewData();
    } catch (err) {
      console.error('Failed to update cost parameters:', err);
    }
  };

  const summary = overview?.summary_cards || {};
  const tableRows = overview?.table_rows || [];
  const costChartData = overview?.cost_chart_data || [];

  // Active selected PLC details from tableRows or fallback
  const activePlcData = tableRows.find((r) => r.plc_id === currentSelectedPlc) || tableRows[0] || {
    plc_id: currentSelectedPlc,
    machine_health: maintenanceData?.machine_health ?? 100,
    main_issue: maintenanceData?.main_issue || 'Normal Operation',
    predicted_rul_days: maintenanceData?.predicted_rul_days ?? '--',
    failure_risk_pct: maintenanceData?.failure_risk_pct ?? 0,
    energy_status: maintenanceData?.energy_status || 'Normal',
    preventive_cost: maintenanceData?.preventive_cost ?? 8000,
    expected_failure_cost: maintenanceData?.expected_failure_cost ?? 25000,
    potential_savings: maintenanceData?.potential_savings ?? 17000,
    recommended_action: maintenanceData?.recommended_action || 'Continue Normal Operation',
    priority_level: maintenanceData?.priority_level || 'Low',
    priority_symbol: maintenanceData?.priority_symbol || '🟢',
    human_readable_alert: maintenanceData?.human_readable_alert || '',
    total_recommendation_summary: maintenanceData?.total_recommendation_summary || '',
    why_recommendation: maintenanceData?.why_recommendation || []
  };

  const getPriorityBadgeClass = (pLevel) => {
    switch (pLevel) {
      case 'Critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'High':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'Medium':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* 8 DASHBOARD SUMMARY CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-3">
        {/* Card 1: Machines Requiring Maintenance */}
        <MetricCard
          title="Machines Requiring Maintenance"
          value={summary.machines_requiring_maintenance ?? '--'}
          unit="Units"
          icon={Wrench}
          valueColor="text-amber-600"
        />

        {/* Card 2: Critical PLCs */}
        <MetricCard
          title="Critical PLCs"
          value={summary.critical_plcs ?? '--'}
          unit="Critical"
          icon={AlertCircle}
          valueColor="text-red-600"
        />

        {/* Card 3: Average RUL */}
        <MetricCard
          title="Average RUL Across Fleet"
          value={summary.avg_rul_days ?? '--'}
          unit="Days"
          icon={Calendar}
          valueColor="text-blue-600"
        />

        {/* Card 4: Estimated Maintenance Cost */}
        <MetricCard
          title="Total Preventive Servicing Cost"
          value={`₹${(summary.total_preventive_cost || 0).toLocaleString()}`}
          unit="INR"
          icon={DollarSign}
          valueColor="text-blue-700"
        />

        {/* Card 5: Expected Failure Cost */}
        <MetricCard
          title="Expected Breakdown Failure Cost"
          value={`₹${(summary.total_expected_failure_cost || 0).toLocaleString()}`}
          unit="INR Risk"
          icon={AlertTriangle}
          valueColor="text-rose-600"
        />

        {/* Card 6: Potential Cost Savings */}
        <MetricCard
          title="Potential Preventive Cost Savings"
          value={`₹${(summary.total_potential_savings || 0).toLocaleString()}`}
          unit="INR Net"
          icon={TrendingUp}
          valueColor="text-emerald-600"
        />

        {/* Card 7: Energy Inefficiency Count */}
        <MetricCard
          title="Energy Inefficient Machines"
          value={summary.energy_inefficiency_count ?? '--'}
          unit="Units (>8% excess)"
          icon={Zap}
          valueColor="text-amber-600"
        />

        {/* Card 8: Estimated Additional Energy Cost */}
        <MetricCard
          title="Additional Energy Loss Cost"
          value={`₹${(summary.total_additional_energy_cost_per_day || 0).toLocaleString()}`}
          unit="INR / day"
          icon={Activity}
          valueColor="text-red-700"
        />
      </div>

      {/* PLC-WISE MAINTENANCE TABLE */}
      <div className="industrial-card p-4 bg-white rounded-xl border border-gray-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between border-b border-gray-100 pb-3">
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-blue-600" />
            <h3 className="text-sm font-bold text-gray-900">PLC-Wise Maintenance & Energy Decision Matrix</h3>
          </div>
          <span className="text-xs text-gray-500 font-semibold bg-gray-100 px-2.5 py-1 rounded">
            Click any row to view machine deep dive
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-900 text-white font-semibold">
                <th className="p-2.5 rounded-l">PLC</th>
                <th className="p-2.5">Health</th>
                <th className="p-2.5">Main Issue</th>
                <th className="p-2.5">RUL</th>
                <th className="p-2.5">Failure Risk</th>
                <th className="p-2.5">Energy Status</th>
                <th className="p-2.5">Preventive Cost</th>
                <th className="p-2.5">Expected Failure Cost</th>
                <th className="p-2.5">Potential Saving</th>
                <th className="p-2.5 rounded-r">Recommendation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 font-medium">
              {tableRows.map((row) => {
                const isSelected = row.plc_id === currentSelectedPlc;
                return (
                  <tr
                    key={row.plc_id}
                    onClick={() => setCurrentSelectedPlc(row.plc_id)}
                    className={`cursor-pointer transition-colors ${
                      isSelected ? 'bg-blue-50/80 font-bold border-l-4 border-blue-600' : 'hover:bg-gray-50'
                    }`}
                  >
                    <td className="p-2.5 font-bold text-gray-900">
                      <div className="flex items-center space-x-1.5">
                        <span>{row.priority_symbol}</span>
                        <span>{row.plc_id}</span>
                      </div>
                    </td>
                    <td className="p-2.5">
                      <span className={`font-mono ${row.machine_health < 50 ? 'text-red-600 font-bold' : row.machine_health < 75 ? 'text-amber-600' : 'text-emerald-600'}`}>
                        {row.machine_health.toFixed(1)}%
                      </span>
                    </td>
                    <td className="p-2.5 text-gray-800 max-w-[180px] truncate" title={row.main_issue}>
                      {row.main_issue}
                    </td>
                    <td className="p-2.5 font-mono text-blue-700">{row.predicted_rul_days} Days</td>
                    <td className="p-2.5 font-mono">{row.failure_risk_pct.toFixed(1)}%</td>
                    <td className="p-2.5">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                        row.energy_inefficiency_pct > 12
                          ? 'bg-rose-100 text-rose-800'
                          : row.energy_inefficiency_pct > 0
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}>
                        {row.energy_inefficiency_pct > 0 ? `+${row.energy_inefficiency_pct}%` : 'Normal'}
                      </span>
                    </td>
                    <td className="p-2.5 font-mono text-gray-700">₹{row.preventive_cost.toLocaleString()}</td>
                    <td className="p-2.5 font-mono text-rose-600 font-semibold">₹{row.expected_failure_cost.toLocaleString()}</td>
                    <td className="p-2.5 font-mono text-emerald-600 font-semibold">
                      {row.potential_savings > 0 ? `₹${row.potential_savings.toLocaleString()}` : '₹0'}
                    </td>
                    <td className="p-2.5">
                      <span className={`px-2 py-0.5 rounded border text-[11px] font-bold ${getPriorityBadgeClass(row.priority_level)}`}>
                        {row.recommended_action}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* MAINTENANCE COST CHART & ENERGY MONITORING CHART */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MaintenanceCostPlot costChartData={costChartData} />
        <EnergyMonitoringPlot
          energyData={energyInfo}
          selectedPlc={currentSelectedPlc}
          setSelectedPlc={setCurrentSelectedPlc}
          plcsList={tableRows}
        />
      </div>

      {/* COST CONFIGURATION CONTROL AREA */}
      <CostConfigDrawer costConfig={overview?.cost_config} onSaveConfig={handleSaveCostConfig} />

      {/* SELECTED PLC DEEP DIVE & TRANSPARENT EVIDENCE SECTION */}
      <div className="industrial-card p-5 bg-white rounded-xl border border-gray-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-gray-100 pb-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-bold text-gray-900">
              Selected Unit Intelligence & Technical Transparency — {activePlcData.plc_id}
            </h3>
          </div>
          <span className={`px-2.5 py-1 text-xs font-bold rounded border ${getPriorityBadgeClass(activePlcData.priority_level)}`}>
            {activePlcData.priority_symbol} Priority: {activePlcData.priority_level}
          </span>
        </div>

        {/* Human Readable Alert Box */}
        <div className="bg-slate-900 text-white p-4 rounded-xl space-y-2">
          <div className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center space-x-1.5">
            <Info className="w-4 h-4" />
            <span>Human-Readable Maintenance Summary Alert</span>
          </div>
          <p className="text-sm font-mono whitespace-pre-line text-slate-100">
            {activePlcData.human_readable_alert || activePlcData.total_recommendation_summary}
          </p>
        </div>

        {/* Combined Decision Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-2 text-xs">
            <h4 className="font-bold text-gray-900 uppercase tracking-wider flex items-center space-x-1.5 border-b pb-1">
              <DollarSign className="w-4 h-4 text-emerald-600" />
              <span>Financial Decision Assessment</span>
            </h4>
            <div>
              <span className="text-gray-500 block">Preventive Maintenance Cost:</span>
              <span className="font-mono font-bold text-gray-900">₹{activePlcData.preventive_cost?.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-500 block">Expected Breakdown Failure Cost:</span>
              <span className="font-mono font-bold text-rose-600">₹{activePlcData.expected_failure_cost?.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-500 block">Potential Cost Savings:</span>
              <span className="font-mono font-bold text-emerald-600">
                {activePlcData.potential_savings > 0 ? `₹${activePlcData.potential_savings?.toLocaleString()}` : '₹0 (Not cost-effective)'}
              </span>
            </div>
            <div className="pt-1 text-[11px] font-medium text-gray-700 bg-white p-2 rounded border border-gray-200">
              {activePlcData.cost_decision_msg}
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 space-y-2 text-xs">
            <h4 className="font-bold text-gray-900 uppercase tracking-wider flex items-center space-x-1.5 border-b pb-1">
              <HelpCircle className="w-4 h-4 text-indigo-600" />
              <span>Why this recommendation? (Model & Calculation Evidence)</span>
            </h4>
            {activePlcData.why_recommendation && activePlcData.why_recommendation.length > 0 ? (
              <ul className="space-y-1.5 text-gray-700 font-medium">
                {activePlcData.why_recommendation.map((bullet, idx) => (
                  <li key={idx} className="flex items-start space-x-1.5">
                    <span className="text-blue-600 font-bold">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">All sensor readings, RUL predictions, and electrical parameters are within normal baseline thresholds.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MaintenanceDashboard;
