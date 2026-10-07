import React, { useState, useEffect } from 'react';
import { Eye, CheckCircle, AlertTriangle, XCircle, ShieldCheck, ShieldAlert, ArrowRight } from 'lucide-react';
import { getVisualInspectionResult } from '../services/api';

const VisualInspectionCard = ({ selectedPlc = 'PLC_01', onViewDetails }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const fetchVisual = async () => {
      try {
        const res = await getVisualInspectionResult(selectedPlc);
        if (mounted) setData(res);
      } catch (err) {
        console.error('Failed to fetch visual card data:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchVisual();
    return () => { mounted = false; };
  }, [selectedPlc]);

  if (loading) {
    return (
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm animate-pulse h-48 flex items-center justify-center">
        <span className="text-xs text-gray-400 font-medium">Loading Visual Health...</span>
      </div>
    );
  }

  const visStatus = data?.visual_status || 'HEALTHY';
  const score = data?.visual_health_score ?? 100;
  const refSim = data?.reference_similarity;
  const sensRel = data?.sensor_reliability || { status: 'RELIABLE' };

  const badgeColors = {
    HEALTHY: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    WARNING: 'bg-amber-100 text-amber-800 border-amber-200',
    CRITICAL: 'bg-rose-100 text-rose-800 border-rose-200',
    UNCERTAIN: 'bg-gray-100 text-gray-800 border-gray-200'
  };

  return (
    <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Eye className="w-5 h-5 text-blue-600" />
          <h3 className="text-sm font-bold text-gray-900">YOLO11 Visual Inspection</h3>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${badgeColors[visStatus]}`}>
          {visStatus}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 py-2 border-y border-gray-100 text-center">
        <div>
          <span className="text-[10px] text-gray-500 uppercase font-semibold block">Visual Health</span>
          <span className="text-lg font-extrabold text-gray-900">{score}%</span>
        </div>
        <div>
          <span className="text-[10px] text-gray-500 uppercase font-semibold block">Gold Ref Similarity</span>
          <span className="text-lg font-extrabold text-gray-900">{refSim != null ? `${refSim}%` : 'N/A'}</span>
        </div>
        <div>
          <span className="text-[10px] text-gray-500 uppercase font-semibold block">Sensor Reliability</span>
          <span className="text-lg font-extrabold text-gray-900">{sensRel.score ?? 100}%</span>
        </div>
      </div>

      <p className="text-xs text-gray-600 line-clamp-2 leading-tight">
        {data?.reason || 'Component aligns with verified healthy baseline.'}
      </p>

      {onViewDetails && (
        <button
          onClick={onViewDetails}
          className="w-full text-xs text-blue-600 font-bold hover:text-blue-700 flex items-center justify-center space-x-1 pt-1"
        >
          <span>Open Full Visual Inspection Module</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
};

export default VisualInspectionCard;
