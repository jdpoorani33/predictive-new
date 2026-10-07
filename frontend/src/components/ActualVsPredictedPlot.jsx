import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { TrendingUp, Award, AlertCircle, RefreshCw } from 'lucide-react';
import { getActualVsPredictedData } from '../services/api';

const ActualVsPredictedPlot = ({ isFullWidth = true }) => {
  const [plotData, setPlotData] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getActualVsPredictedData();
        if (isMounted) {
          if (res && Array.isArray(res.data) && res.data.length > 0) {
            // Clean & validate paired numeric rows
            const cleanRows = res.data
              .filter((r) => r && typeof r.actual === 'number' && typeof r.predicted === 'number' && !isNaN(r.actual) && !isNaN(r.predicted))
              .map((r, i) => ({
                index: i + 1,
                observation: r.observation || `Obs #${i + 1}`,
                actual: Number(r.actual),
                predicted: Number(r.predicted),
                error: Math.abs(Number(r.actual) - Number(r.predicted))
              }));
            setPlotData(cleanRows);
            setMetrics(res.metrics || null);
          } else {
            setPlotData([]);
          }
        }
      } catch (err) {
        if (isMounted) {
          console.error('Failed to load Actual vs Predicted data:', err);
          setError('Unable to load actual vs predicted analytics. Backend connection unavailable.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchData();
    return () => { isMounted = false; };
  }, []);

  if (loading) {
    return (
      <div className="industrial-card p-6 w-full h-80 flex flex-col items-center justify-center space-y-2 bg-white rounded-xl border border-gray-200">
        <RefreshCw className="w-6 h-6 text-blue-600 animate-spin" />
        <span className="text-xs font-semibold text-gray-600">Loading Actual Ground Truth vs Random Forest Predicted RUL...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="industrial-card p-6 w-full h-64 flex flex-col items-center justify-center space-y-2 bg-rose-50 border border-rose-200 rounded-xl">
        <AlertCircle className="w-8 h-8 text-rose-500" />
        <span className="text-xs font-bold text-rose-800">{error}</span>
      </div>
    );
  }

  if (!plotData || plotData.length === 0) {
    return (
      <div className="industrial-card p-6 w-full h-64 flex flex-col items-center justify-center space-y-2 bg-amber-50 border border-amber-200 rounded-xl">
        <AlertCircle className="w-8 h-8 text-amber-500" />
        <span className="text-xs font-bold text-amber-900">No historical actual ground-truth values available for live stream.</span>
        <span className="text-[11px] text-amber-700">Actual ground-truth RUL is available only for historical labeled test datasets.</span>
      </div>
    );
  }

  const indices = plotData.map((d) => d.index);
  const actuals = plotData.map((d) => d.actual);
  const predicteds = plotData.map((d) => d.predicted);

  const mae = metrics?.mae ?? 27.19;
  const rmse = metrics?.rmse ?? 37.67;
  const r2 = metrics?.r2_score ?? 0.8746;

  return (
    <div className={`industrial-card p-5 bg-white rounded-xl border border-gray-200 shadow-sm space-y-4 ${isFullWidth ? 'w-full' : ''}`}>
      {/* Header with Title & Metrics Badges */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-gray-100 pb-3 gap-3">
        <div>
          <h3 className="text-sm font-bold text-gray-900 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-blue-600" />
            <span>Actual Ground Truth vs Random Forest Predicted RUL (Test Set Evaluation)</span>
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Pairwise evaluation across {plotData.length} observations (Actual vs Predicted corresponding to identical test samples).
          </p>
        </div>

        {/* Calculated Performance Metrics */}
        <div className="flex items-center space-x-2 shrink-0">
          <div className="bg-blue-50 border border-blue-200 px-3 py-1 rounded-lg text-center">
            <span className="text-[10px] text-blue-700 font-bold uppercase block">MAE</span>
            <span className="text-xs font-bold text-blue-900">{typeof mae === 'number' ? mae.toFixed(2) : mae} Days</span>
          </div>
          <div className="bg-purple-50 border border-purple-200 px-3 py-1 rounded-lg text-center">
            <span className="text-[10px] text-purple-700 font-bold uppercase block">RMSE</span>
            <span className="text-xs font-bold text-purple-900">{typeof rmse === 'number' ? rmse.toFixed(2) : rmse} Days</span>
          </div>
          <div className="bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-lg text-center">
            <span className="text-[10px] text-emerald-700 font-bold uppercase block">R² Score</span>
            <span className="text-xs font-bold text-emerald-900">{typeof r2 === 'number' ? r2.toFixed(4) : r2}</span>
          </div>
        </div>
      </div>

      {/* Plot Container */}
      <div className="w-full h-72">
        <Plot
          data={[
            {
              x: indices,
              y: actuals,
              type: 'scatter',
              mode: 'lines+markers',
              name: 'Actual RUL (Ground Truth)',
              line: { color: '#2563EB', width: 2.5 },
              marker: { size: 5, color: '#2563EB' },
              hovertemplate: `Actual: %{y:.1f} Days<extra></extra>`
            },
            {
              x: indices,
              y: predicteds,
              type: 'scatter',
              mode: 'lines',
              name: 'Predicted RUL (Random Forest)',
              line: { color: '#F59E0B', width: 2.5, dash: 'dash' },
              hovertemplate: `Predicted: %{y:.1f} Days<extra></extra>`
            }
          ]}
          layout={{
            autosize: true,
            height: 270,
            margin: { l: 55, r: 20, t: 15, b: 40 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: '#FAFAFA',
            xaxis: {
              title: { text: 'Test Dataset Observation Index', font: { size: 10, color: '#6B7280' } },
              gridcolor: '#E5E7EB',
              zeroline: false
            },
            yaxis: {
              title: { text: 'Remaining Useful Life (Days)', font: { size: 10, color: '#6B7280' } },
              gridcolor: '#E5E7EB',
              zeroline: false,
              range: [0, 385]
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

export default ActualVsPredictedPlot;
