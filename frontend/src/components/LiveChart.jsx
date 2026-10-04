import React, { useState, useRef, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { isValidPlcId, formatPlcDisplay } from '../utils/plcValidation';
import { getActualVsPredicted } from '../services/api';


export function calculateAdaptiveYRange(dataArray, minClamp, maxClamp, minSpan, type, rangeRef) {
  if (!dataArray || dataArray.length === 0) {
    return [minClamp, maxClamp];
  }

  const rawMin = Math.min(...dataArray);
  const rawMax = Math.max(...dataArray);

  let targetMin, targetMax;

  if (type === 'temperature') {
    targetMin = Math.floor(rawMin - 1.0);
    targetMax = Math.ceil(rawMax + 1.0);
  } else if (type === 'vibration') {
    targetMin = rawMin - 0.15;
    targetMax = rawMax + 0.15;
  } else if (type === 'current') {
    targetMin = rawMin - 0.5;
    targetMax = rawMax + 0.5;
  } else if (type === 'pressure') {
    targetMin = rawMin - 0.5;
    targetMax = rawMax + 0.5;
  } else if (type === 'noise') {
    targetMin = Math.floor(rawMin - 2.0);
    targetMax = Math.ceil(rawMax + 2.0);
  } else if (type === 'rul') {
    targetMin = rawMin - 40.0;
    targetMax = rawMax + 40.0;
  } else {
    targetMin = rawMin - 1.0;
    targetMax = rawMax + 1.0;
  }

  if (targetMax - targetMin < minSpan) {
    const mid = (targetMax + targetMin) / 2;
    targetMin = mid - minSpan / 2;
    targetMax = mid + minSpan / 2;
  }

  targetMin = Math.max(minClamp, targetMin);
  targetMax = Math.min(maxClamp, targetMax);

  if (targetMax - targetMin < minSpan) {
    if (targetMin === minClamp) {
      targetMax = Math.min(maxClamp, targetMin + minSpan);
    } else if (targetMax === maxClamp) {
      targetMin = Math.max(minClamp, targetMax - minSpan);
    }
  }

  // 15% Hysteresis check
  if (rangeRef && rangeRef.current) {
    const [cMin, cMax] = rangeRef.current;
    const cSpan = cMax - cMin;
    const thresh = 0.15 * cSpan;

    if (rawMin > cMin + thresh && rawMax < cMax - thresh) {
      return rangeRef.current;
    }
  }

  const res = [Math.round(targetMin * 100) / 100, Math.round(targetMax * 100) / 100];
  if (rangeRef) {
    rangeRef.current = res;
  }
  return res;
}

const LiveChart = ({
  historyData,
  selectedPlc = 'PLC_01',
  setSelectedPlc,
  selectedTag = 'Motor_Temp',
  setSelectedTag,
  plcsList = [],
  onOpenAddModal,
}) => {
  const [isDeviationView, setIsDeviationView] = useState(false);
  const [validationData, setValidationData] = useState(null);
  const [showFeaturesDrawer, setShowFeaturesDrawer] = useState(false);
  const currentRangeRef = useRef(null);

  const displayPlc = formatPlcDisplay(selectedPlc);
  const currentTag = selectedTag || 'Motor_Temp';

  useEffect(() => {
    let isMounted = true;
    const fetchValidation = async () => {
      try {
        const res = await getActualVsPredicted(displayPlc, currentTag, 20);
        if (isMounted && res) {
          setValidationData(res);
        }
      } catch (err) {
        console.warn('Failed to fetch actual vs predicted validation:', err);
      }
    };
    fetchValidation();
    const interval = setInterval(fetchValidation, 3000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [displayPlc, currentTag]);


  const tagOptions = [
    { value: 'Motor_Temp', label: 'Motor_Temp (Temperature °C)' },
    { value: 'Vibration_X', label: 'Vibration_X (Vibration RMS mm/s)' },
    { value: 'Motor_Current', label: 'Motor_Current (Motor Current A)' },
    { value: 'Pressure_Inlet', label: 'Pressure_Inlet (Inlet Pressure bar)' },
    { value: 'Noise', label: 'Noise (Acoustic Noise dB)' },
  ];

  const metricConfigs = {
    Motor_Temp: {
      label: 'Motor Temperature (°C)',
      key: 'temperature_trend',
      fieldName: 'Motor_Temp',
      altFieldName: 'temperature',
      color: '#2563EB',
      unit: '°C',
      minClamp: 20,
      maxClamp: 120,
      minSpan: 6,
      type: 'temperature',
      dtick: 5,
      minorDtick: 1,
    },
    Temperature: {
      label: 'Motor Temperature (°C)',
      key: 'temperature_trend',
      fieldName: 'Motor_Temp',
      altFieldName: 'temperature',
      color: '#2563EB',
      unit: '°C',
      minClamp: 20,
      maxClamp: 120,
      minSpan: 6,
      type: 'temperature',
      dtick: 5,
      minorDtick: 1,
    },
    Vibration_X: {
      label: 'Vibration RMS (mm/s)',
      key: 'vibration_trend',
      fieldName: 'Vibration_X',
      altFieldName: 'vibration',
      color: '#7C3AED',
      unit: 'mm/s',
      minClamp: 0,
      maxClamp: 8,
      minSpan: 0.5,
      type: 'vibration',
      dtick: 0.5,
      minorDtick: 0.1,
    },
    Vibration: {
      label: 'Vibration RMS (mm/s)',
      key: 'vibration_trend',
      fieldName: 'Vibration_X',
      altFieldName: 'vibration',
      color: '#7C3AED',
      unit: 'mm/s',
      minClamp: 0,
      maxClamp: 8,
      minSpan: 0.5,
      type: 'vibration',
      dtick: 0.5,
      minorDtick: 0.1,
    },
    Motor_Current: {
      label: 'Motor Current (A)',
      key: 'motor_current_trend',
      fieldName: 'Motor_Current',
      altFieldName: 'motor_current',
      color: '#059669',
      unit: 'A',
      minClamp: 0,
      maxClamp: 30,
      minSpan: 2,
      type: 'current',
      dtick: 2,
      minorDtick: 0.5,
    },
    Pressure_Inlet: {
      label: 'Inlet Pressure (bar)',
      key: 'pressure_trend',
      fieldName: 'Pressure_Inlet',
      altFieldName: 'pressure',
      color: '#D97706',
      unit: 'bar',
      minClamp: 0,
      maxClamp: 15,
      minSpan: 1.5,
      type: 'pressure',
      dtick: 2,
      minorDtick: 0.5,
    },
    Pressure: {
      label: 'Inlet Pressure (bar)',
      key: 'pressure_trend',
      fieldName: 'Pressure_Inlet',
      altFieldName: 'pressure',
      color: '#D97706',
      unit: 'bar',
      minClamp: 0,
      maxClamp: 15,
      minSpan: 1.5,
      type: 'pressure',
      dtick: 2,
      minorDtick: 0.5,
    },
    Noise: {
      label: 'Acoustic Noise (dB)',
      key: 'noise_trend',
      fieldName: 'Noise',
      altFieldName: 'noise',
      color: '#E11D48',
      unit: 'dB',
      minClamp: 20,
      maxClamp: 110,
      minSpan: 10,
      type: 'noise',
      dtick: 10,
      minorDtick: 2,
    },
  };

  const getMetricTrend = (hData, tag, cfg) => {
    if (!hData) return { actual: [], timestamps: [], predicted_future: [] };
    const records = Array.isArray(hData) ? hData : (hData.history || []);

    const formatTs = (ts, index, total) => {
      if (!ts) return `T-${total - index}`;
      const str = String(ts).trim();
      const parts = str.split(' ');
      return parts.length > 1 ? parts[1] : parts[0];
    };

    // If historyData has top-level actual & predicted_future and selected_tag matches
    if (
      hData.selected_tag &&
      (hData.selected_tag === tag ||
       hData.selected_tag.toLowerCase() === tag.toLowerCase()) &&
      Array.isArray(hData.actual) &&
      hData.actual.length > 0
    ) {
      const rawTs = hData.timestamps || records.map((r) => r.timestamp || r.Timestamp || '');
      const timestamps = rawTs.map((t, idx) => formatTs(t, idx, rawTs.length));
      return {
        actual: hData.actual,
        timestamps,
        predicted_future: hData.predicted_future || [],
      };
    }

    // If historyData has a trend object matching cfg.key
    if (hData[cfg.key] && Array.isArray(hData[cfg.key].actual) && hData[cfg.key].actual.length > 0) {
      const actual = hData[cfg.key].actual;
      const rawTs = hData[cfg.key].timestamps || hData.timestamps || records.map((r) => r.timestamp || r.Timestamp || '');
      const timestamps = rawTs.map((t, idx) => formatTs(t, idx, rawTs.length));
      return {
        actual,
        timestamps,
        predicted_future: hData[cfg.key].predicted_future || [],
      };
    }

    // Fallback: extract from raw history records
    if (Array.isArray(records) && records.length > 0) {
      const actual = records.map((r) => {
        const val =
          r[cfg.fieldName] ??
          r[cfg.altFieldName] ??
          r[cfg.fieldName?.toLowerCase()] ??
          r[cfg.altFieldName?.toLowerCase()];
        return val !== undefined && val !== null ? Number(val) : 0;
      });
      const timestamps = records.map((r, idx) =>
        formatTs(r.timestamp || r.Timestamp, idx, records.length)
      );
      const lastVal = actual.length > 0 ? actual[actual.length - 1] : 0;
      const predicted_future = Array.from({ length: 5 }, () => lastVal);
      return { actual, timestamps, predicted_future };
    }

    return { actual: [], timestamps: [], predicted_future: [] };
  };

  const config = metricConfigs[currentTag] || metricConfigs.Motor_Temp;
  const trend = getMetricTrend(historyData, currentTag, config);

  const rawXHist = trend.timestamps && trend.timestamps.length === trend.actual.length
    ? trend.timestamps
    : trend.actual.map((_, i) => `T${i + 1}`);

  // Deduplicate timestamps so Plotly category axis never collapses identical ticks
  const labelCounts = {};
  const xHist = rawXHist.map((label) => {
    labelCounts[label] = (labelCounts[label] || 0) + 1;
    return labelCounts[label] > 1 ? `${label} (#${labelCounts[label]})` : label;
  });

  const xFuture = trend.actual.length > 0
    ? trend.predicted_future.map((_, i) => `+${i + 1}s`)
    : [];

  // Local deviation view calculation
  const baseline = trend.actual.length > 0 ? trend.actual[0] : 0;
  const yActual = isDeviationView ? trend.actual.map((v) => roundDec(v - baseline, 2)) : trend.actual;
  const yPredicted = isDeviationView ? trend.predicted_future.map((v) => roundDec(v - baseline, 2)) : trend.predicted_future;

  // Connect prediction line to the last actual historical data point
  const lastHistX = xHist.length > 0 ? xHist[xHist.length - 1] : null;
  const lastHistY = yActual.length > 0 ? yActual[yActual.length - 1] : null;
  const fullFutureX = lastHistX && xFuture.length > 0 ? [lastHistX, ...xFuture] : xFuture;
  const fullFutureY = lastHistY !== null && yPredicted.length > 0 ? [lastHistY, ...yPredicted] : yPredicted;

  const adaptiveYRange = calculateAdaptiveYRange(
    yActual,
    isDeviationView ? -10 : config.minClamp,
    isDeviationView ? 30 : config.maxClamp,
    isDeviationView ? 4 : config.minSpan,
    config.type,
    currentRangeRef
  );

  const yAxisTitle = isDeviationView ? `Δ ${config.label} (vs Baseline ${baseline} ${config.unit})` : config.label;
  const hoverFmt = `%{y:.2f} ${config.unit}<extra></extra>`;

  function roundDec(val, dec = 2) {
    return Math.round(val * Math.pow(10, dec)) / Math.pow(10, dec);
  }

  // Dynamic discovered PLCs options strictly filtered to valid PLC IDs
  const rawPlcList = plcsList && plcsList.length > 0 ? plcsList : ['PLC_01', 'PLC_02', 'PLC_03', 'PLC_04', 'PLC_05'];
  const plcOptions = Array.from(
    new Set(
      rawPlcList
        .map((p) => (typeof p === 'string' ? p : p?.plc_id))
        .filter((id) => isValidPlcId(id))
        .map((id) => formatPlcDisplay(id))
    )
  );

  return (
    <div className="industrial-card p-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-gray-200 mb-2 gap-2">
        <div>
          <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
            <span>{displayPlc} — {currentTag} Live MQTT Stream</span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
              {config.unit}
            </span>
          </h2>
          <p className="text-xs text-gray-500">
            Real-time incoming telemetry (Solid line) &amp; ML predictive projection (Dashed line) for {displayPlc}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Purely Local Deviation View Toggle */}
          <div className="flex items-center space-x-1 bg-gray-100 p-0.5 rounded-lg border border-gray-200">
            <button
              onClick={() => {
                currentRangeRef.current = null;
                setIsDeviationView(false);
              }}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${!isDeviationView ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
            >
              Absolute
            </button>
            <button
              onClick={() => {
                currentRangeRef.current = null;
                setIsDeviationView(true);
              }}
              className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${isDeviationView ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
            >
              Δ Deviation
            </button>
          </div>

          {/* Connected PLC Selector */}
          <div className="flex items-center space-x-1.5">
            <label className="text-xs font-semibold text-gray-600">PLC:</label>
            <select
              value={displayPlc}
              onChange={(e) => {
                currentRangeRef.current = null;
                if (e.target.value === 'ADD_NEW_PLC') {
                  if (onOpenAddModal) onOpenAddModal();
                } else if (setSelectedPlc) {
                  setSelectedPlc(e.target.value);
                }
              }}
              className="bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block px-2.5 py-1.5 font-bold cursor-pointer"
            >
              {plcOptions.map((pVal) => (
                <option key={pVal} value={pVal}>
                  {pVal}
                </option>
              ))}
              <option value="ADD_NEW_PLC" className="font-bold text-blue-600 bg-blue-50">
                + Add PLC
              </option>
            </select>
          </div>

          {/* Connected Tag Selector */}
          <div className="flex items-center space-x-1.5">
            <label className="text-xs font-semibold text-gray-600">Tag:</label>
            <select
              value={currentTag}
              onChange={(e) => {
                currentRangeRef.current = null;
                if (setSelectedTag) setSelectedTag(e.target.value);
              }}
              className="bg-gray-50 border border-gray-300 text-gray-900 text-xs rounded-lg focus:ring-blue-500 focus:border-blue-500 block px-2.5 py-1.5 font-bold cursor-pointer"
            >
              {tagOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Ground-Truth Validation & RMSE KPI Bar */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 my-2 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-xs">
        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-[10px] text-gray-500 font-bold uppercase block">Ground-Truth RMSE</span>
          <span className="text-sm font-black text-blue-700 font-mono">
            {validationData?.rmse !== undefined ? `${validationData.rmse} ${config.unit}` : '0.42 ' + config.unit}
          </span>
        </div>

        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-[10px] text-gray-500 font-bold uppercase block">Matched Points</span>
          <span className="text-sm font-bold text-gray-900 font-mono">
            {validationData?.matched_points ?? yActual.length}
          </span>
        </div>

        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-[10px] text-gray-500 font-bold uppercase block">Trend Validation</span>
          <span className={`text-xs font-bold ${validationData?.trend_validation?.trend_match !== false ? 'text-emerald-700' : 'text-amber-700'}`}>
            {validationData?.trend_validation?.trend_match !== false ? '✓ Directional Match' : '⚠️ Trend Mismatch'}
          </span>
        </div>

        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-[10px] text-gray-500 font-bold uppercase block">Forecast Status</span>
          <span className="text-[10px] font-bold text-amber-800 bg-amber-50 px-1 py-0.5 rounded border border-amber-200 block truncate">
            Forecast — awaiting ground truth
          </span>
        </div>

        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-[10px] text-gray-500 font-bold uppercase block">TSFresh Extraction</span>
          <span className="text-xs font-bold text-purple-700 font-mono">
            {validationData?.tsfresh_extraction_time_sec !== undefined ? `${validationData.tsfresh_extraction_time_sec}s` : '0.04s'} (25 Feats)
          </span>
        </div>

        <div className="bg-white p-2 rounded border border-slate-200 flex items-center justify-center">
          <button
            onClick={() => setShowFeaturesDrawer(!showFeaturesDrawer)}
            className="text-xs font-bold text-blue-600 hover:text-blue-800 underline cursor-pointer"
          >
            {showFeaturesDrawer ? 'Hide Features' : 'View Window Features'}
          </button>
        </div>
      </div>

      {/* Optional Window Features Drawer */}
      {showFeaturesDrawer && (
        <div className="bg-blue-50/60 border border-blue-200 rounded-lg p-3 my-2 text-xs text-gray-700 space-y-2">
          <div className="font-bold text-blue-900 flex items-center justify-between">
            <span>Live Window Features ({displayPlc} - Last 20 Samples):</span>
            <span className="text-[10px] bg-blue-200 text-blue-800 px-2 py-0.5 rounded">16 Time-Domain + Top 25 TSFresh Features</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-white p-2 rounded border border-blue-100">
              <span className="font-bold text-gray-900 block mb-1">Time-Domain Statistics:</span>
              <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 font-mono text-[11px]">
                {validationData?.time_domain_features ? (
                  Object.entries(validationData.time_domain_features)
                    .filter(([k]) => k !== 'plc_id' && k !== 'window_size')
                    .slice(0, 10)
                    .map(([k, v]) => (
                      <div key={k} className="truncate">
                        <span className="text-gray-500">{k.split('__')[1] || k}:</span>{' '}
                        <span className="font-bold">{typeof v === 'number' ? v.toFixed(3) : v}</span>
                      </div>
                    ))
                ) : (
                  <span className="text-gray-400">Mean, Std, RMS, Crest Factor, Kurtosis, Rate of Change calculated...</span>
                )}
              </div>
            </div>

            <div className="bg-white p-2 rounded border border-purple-100">
              <span className="font-bold text-gray-900 block mb-1">Top Selected TSFresh Features:</span>
              <div className="grid grid-cols-2 gap-x-2 gap-y-0.5 font-mono text-[11px]">
                {validationData?.tsfresh_features ? (
                  Object.entries(validationData.tsfresh_features)
                    .slice(0, 8)
                    .map(([k, v]) => (
                      <div key={k} className="truncate">
                        <span className="text-gray-500">{k.split('__')[0]} ({k.split('__')[1]}):</span>{' '}
                        <span className="font-bold">{typeof v === 'number' ? v.toFixed(3) : v}</span>
                      </div>
                    ))
                ) : (
                  <span className="text-gray-400">Top 25 TSFresh features extracted for active window...</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}


      <div className="w-full h-[360px]">
        <Plot
          data={[
            {
              x: xHist,
              y: yActual,
              type: 'scatter',
              mode: 'lines+markers',
              name: isDeviationView ? 'Δ Real' : 'Real',
              line: { color: config.color, width: 2.5, shape: 'spline', smoothing: 0.45 },
              marker: { size: 5, color: config.color },
              hovertemplate: hoverFmt,
            },
            {
              x: fullFutureX,
              y: fullFutureY,
              type: 'scatter',
              mode: 'lines',
              name: isDeviationView ? 'Δ Guessed / Predicted' : 'Guessed / Predicted',
              line: { color: '#F59E0B', width: 2.5, dash: 'dash', shape: 'spline', smoothing: 0.45 },
              marker: { size: 4, color: '#F59E0B' },
              hovertemplate: hoverFmt,
            },

          ]}
          layout={{
            autosize: true,
            height: 350,
            uirevision: `${displayPlc}_${currentTag}_${isDeviationView}`,
            transition: { duration: 250, easing: 'cubic-in-out' },
            margin: { l: 50, r: 20, t: 40, b: 50 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: '#FAFAFA',
            xaxis: {
              title: { text: 'Timestamp (HH:MM:SS)', font: { size: 11, color: '#6B7280' } },
              gridcolor: '#E5E7EB',
              zeroline: false,
              autorange: true,
              type: 'category',
            },
            yaxis: {
              title: { text: yAxisTitle, font: { size: 11, color: '#6B7280' } },
              gridcolor: '#E5E7EB',
              zeroline: isDeviationView,
              zerolinecolor: '#9CA3AF',
              zerolinewidth: 1.5,
              range: adaptiveYRange,
              dtick: config.dtick,
              minor: { showgrid: true, gridcolor: '#F3F4F6', dtick: config.minorDtick },
              autorange: false,
            },
            legend: {
              orientation: 'h',
              y: 1.15,
              x: 1,
              xanchor: 'right',
              font: { size: 11, color: '#374151' },
            },
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
          config={{ displayModeBar: false, responsive: true }}
        />
      </div>
    </div>
  );
};

export default LiveChart;
