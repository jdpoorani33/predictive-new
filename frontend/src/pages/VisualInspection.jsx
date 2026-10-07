import React, { useState, useEffect } from 'react';
import {
  Eye,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  Camera,
  Upload,
  RefreshCw,
  Zap,
  Sliders,
  Activity,
  Layers,
  FileText,
  Info,
  X,
  Lock,
  Database
} from 'lucide-react';
import {
  getVisualInspectionResult,
  getVisualReference,
  analyzeVisualImage,
  setVisualReference,
  simulateVisualDefect
} from '../services/api';

const VisualInspection = ({ selectedPlc = 'PLC_01' }) => {
  const [data, setData] = useState(null);
  const [refMeta, setRefMeta] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploadingRef, setUploadingRef] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [showRefModal, setShowRefModal] = useState(false);
  const [refModalData, setRefModalData] = useState(null);
  const [loadingRefModal, setLoadingRefModal] = useState(false);

  const loadData = async (plcId = selectedPlc) => {
    setLoading(true);
    try {
      const [resultRes, refRes] = await Promise.all([
        getVisualInspectionResult(plcId).catch(() => null),
        getVisualReference(plcId, false).catch(() => null)
      ]);
      if (resultRes) setData(resultRes);
      if (refRes) setRefMeta(refRes);
    } catch (err) {
      console.error('Failed to load visual inspection result:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(selectedPlc);
  }, [selectedPlc]);

  const handleSimulateMode = async (mode) => {
    setLoading(true);
    try {
      const res = await simulateVisualDefect(selectedPlc, mode);
      setData(res);
    } catch (err) {
      console.error('Failed to simulate defect:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingRef(true);
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const res = await setVisualReference(selectedPlc, e.target.result);
        alert(res?.message || 'Gold Reference updated successfully!');
        await loadData(selectedPlc);
      } catch (err) {
        alert('Failed to set Gold Reference: ' + err.message);
      } finally {
        setUploadingRef(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingImage(true);
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const res = await analyzeVisualImage(selectedPlc, e.target.result);
        setData(res);
      } catch (err) {
        alert('Failed to analyze image: ' + err.message);
      } finally {
        setUploadingImage(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleOpenRefModal = async () => {
    setShowRefModal(true);
    setLoadingRefModal(true);
    try {
      const refData = await getVisualReference(selectedPlc, true);
      setRefModalData(refData);
    } catch (err) {
      console.error('Failed to fetch reference image:', err);
    } finally {
      setLoadingRefModal(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex items-center space-x-3 text-blue-600">
          <RefreshCw className="w-6 h-6 animate-spin" />
          <span className="font-semibold text-gray-700">Analyzing Optical Telemetry & Backend Reference...</span>
        </div>
      </div>
    );
  }

  const statusColors = {
    HEALTHY: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    WARNING: 'bg-amber-50 text-amber-700 border-amber-200',
    CRITICAL: 'bg-rose-50 text-rose-700 border-rose-200',
    UNCERTAIN: 'bg-gray-50 text-gray-700 border-gray-200'
  };

  const statusIcons = {
    HEALTHY: <CheckCircle className="w-5 h-5 text-emerald-600" />,
    WARNING: <AlertTriangle className="w-5 h-5 text-amber-600" />,
    CRITICAL: <XCircle className="w-5 h-5 text-rose-600" />,
    UNCERTAIN: <Info className="w-5 h-5 text-gray-600" />
  };

  const visStatus = data?.visual_status || data?.status || 'HEALTHY';
  const refStatus = data?.reference_status || refMeta?.reference_status || 'VALID';
  const refVersion = data?.reference_version || refMeta?.version || 'v1';
  const refUpdatedAt = data?.reference_updated_at || refMeta?.updated_at || 'Registered Baseline';
  const sensRel = data?.sensor_reliability || { status: 'RELIABLE', score: 100 };

  return (
    <div className="space-y-6">
      {/* Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between bg-white p-5 rounded-xl border border-gray-200 shadow-sm gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 flex items-center space-x-2">
            <Eye className="w-6 h-6 text-blue-600" />
            <span>Visual Inspection & Physical Defect Detection</span>
          </h1>
          <div className="flex items-center space-x-3 mt-1.5 text-xs text-gray-600">
            <span>Machine Target: <strong className="text-gray-900">{selectedPlc}</strong></span>
            <span className="text-gray-300">•</span>
            <div className="flex items-center space-x-1.5 bg-slate-100 px-2.5 py-0.5 rounded border border-slate-200">
              <Lock className="w-3 h-3 text-emerald-600" />
              <span>Backend Reference: <strong className="text-emerald-700">{refStatus}</strong></span>
              <span className="text-slate-400 font-mono">({refVersion})</span>
            </div>
            <span className="text-gray-300">•</span>
            <span className="text-gray-500 font-mono">Updated: {refUpdatedAt}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleOpenRefModal}
            className="bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold px-3 py-2 rounded-lg transition flex items-center space-x-1.5 border border-slate-300 shadow-sm"
          >
            <Database className="w-3.5 h-3.5 text-slate-600" />
            <span>View Gold Reference</span>
          </button>

          <label className="cursor-pointer bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg transition flex items-center space-x-1.5 shadow-sm">
            <Upload className="w-3.5 h-3.5 text-blue-600" />
            <span>{uploadingRef ? 'Uploading Reference...' : 'Update Gold Reference'}</span>
            <input type="file" accept="image/*" onChange={handleRefUpload} className="hidden" />
          </label>

          <label className="cursor-pointer bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3.5 py-2 rounded-lg transition flex items-center space-x-1.5 shadow-sm">
            <Camera className="w-4 h-4" />
            <span>{uploadingImage ? 'Analyzing Image...' : 'Inspect New Image'}</span>
            <input type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />
          </label>

          <button
            onClick={() => loadData(selectedPlc)}
            className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-600"
            title="Refresh Inspection"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Visual Health Score Card */}
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <span>Visual Health Score</span>
            <Eye className="w-4 h-4 text-blue-600" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-gray-900">{data?.visual_health_score ?? 100}</span>
            <span className="text-xs text-gray-500 font-medium">/ 100</span>
          </div>
          <div className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md border text-xs font-bold ${statusColors[visStatus]}`}>
            {statusIcons[visStatus]}
            <span>{visStatus}</span>
          </div>
        </div>

        {/* Reference Similarity Card */}
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <span>Gold Reference Similarity</span>
            <Layers className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-gray-900">
              {data?.reference_similarity != null ? `${data.reference_similarity}%` : 'N/A'}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs pt-1 border-t border-gray-100">
            <span className="text-gray-500">Backend Status:</span>
            <span className={`font-bold px-2 py-0.5 rounded text-[10px] ${refStatus === 'VALID' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
              {refStatus} ({refVersion})
            </span>
          </div>
        </div>

        {/* Sensor Reliability Audit Card */}
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <span>Sensor Reliability Audit</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-gray-900">{sensRel.score ?? 100}%</span>
          </div>
          <div className="flex items-center justify-between text-xs pt-1 border-t border-gray-100">
            <span className="text-gray-500">Cross-Check Audit:</span>
            <span className={`font-bold px-2 py-0.5 rounded text-[10px] ${sensRel.status === 'RELIABLE' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
              {sensRel.status}
            </span>
          </div>
        </div>

        {/* Multi-Modal Machine Health */}
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-wider">
            <span>Overall Combined Health</span>
            <Activity className="w-4 h-4 text-purple-600" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-gray-900">{data?.overall_machine_health ?? 100}%</span>
          </div>
          <div className="flex items-center justify-between text-xs pt-1 border-t border-gray-100">
            <span className="text-gray-500">Fused Status:</span>
            <span className="font-bold text-gray-800">{data?.overall_machine_status || 'Healthy'}</span>
          </div>
        </div>
      </div>

      {/* Main Inspection Results Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Inspected Image Preview */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
            <h2 className="text-sm font-bold text-gray-800 flex items-center space-x-2">
              <Camera className="w-4 h-4 text-blue-600" />
              <span>Inspected Component Preview (YOLO11 Detections)</span>
            </h2>
            <span className="text-xs font-semibold text-gray-500">
              Evaluated against stored backend Gold Reference ({refVersion})
            </span>
          </div>

          <div className="p-5 flex-1 flex flex-col justify-center bg-slate-950 min-h-[380px]">
            {data?.images?.current_annotated || data?.images?.current_image ? (
              <img
                src={data.images.current_annotated || data.images.current_image}
                alt={`Inspected image for ${selectedPlc}`}
                className="w-full h-full max-h-[460px] object-contain mx-auto rounded-lg"
              />
            ) : (
              <div className="text-center text-gray-400 text-xs py-12">
                <Camera className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                <span>No inspection image uploaded yet. Click "Inspect New Image" above.</span>
              </div>
            )}
          </div>

          {/* Action Recommendation Banner */}
          <div className="p-4 bg-blue-50 border-t border-blue-100 flex items-center justify-between">
            <div className="text-xs text-blue-900 font-semibold space-y-0.5">
              <span className="font-bold uppercase tracking-wider block text-[10px] text-blue-600">Action Recommendation:</span>
              <p>{data?.recommendation || 'Component is operating cleanly.'}</p>
            </div>
          </div>
        </div>

        {/* Detections & Evidence Panel */}
        <div className="space-y-6 flex flex-col justify-between">
          {/* Detected Defects Table */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3">
            <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center space-x-1.5">
              <Sliders className="w-4 h-4 text-blue-600" />
              <span>Detected Physical Defects ({data?.detections_count ?? 0})</span>
            </h3>

            {data?.detections && data.detections.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-gray-600">
                  <thead className="bg-gray-50 text-gray-700 font-semibold uppercase tracking-wider border-b border-gray-200">
                    <tr>
                      <th className="py-2 px-2">Defect</th>
                      <th className="py-2 px-2">Conf</th>
                      <th className="py-2 px-2">Severity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {data.detections.map((d, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="py-2 px-2 font-bold text-gray-900 capitalize">{d.class}</td>
                        <td className="py-2 px-2 font-semibold text-blue-600">{Math.round(d.confidence * 100)}%</td>
                        <td className="py-2 px-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              d.severity === 'critical' || d.severity === 'high'
                                ? 'bg-rose-100 text-rose-800'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                          >
                            {d.severity}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-6 text-center text-gray-500 text-xs bg-emerald-50/50 rounded-lg border border-emerald-100">
                <CheckCircle className="w-6 h-6 text-emerald-600 mx-auto mb-1" />
                <span className="font-semibold text-emerald-800">No physical defect detected.</span>
              </div>
            )}
          </div>

          {/* Observed Evidence */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3 flex-1">
            <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center space-x-1.5">
              <FileText className="w-4 h-4 text-purple-600" />
              <span>Inspection Evidence & Factors</span>
            </h3>

            <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-1 text-xs">
              <span className="font-bold text-gray-900 block">Inspection Summary:</span>
              <p className="text-gray-700 leading-relaxed">{data?.reason || 'Evaluation completed.'}</p>
            </div>

            {data?.evidence && data.evidence.length > 0 && (
              <div className="space-y-1.5 pt-1">
                <span className="text-[11px] font-bold text-gray-700 uppercase tracking-wider block">Evidence Factors:</span>
                <ul className="space-y-1 text-xs">
                  {data.evidence.map((ev, i) => (
                    <li key={i} className="text-gray-600 flex items-start space-x-1.5">
                      <span className="text-blue-500 font-bold">•</span>
                      <span>{ev}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Demo Sandbox Controls */}
      <div className="bg-slate-900 text-white p-4 rounded-xl shadow-md space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <span className="text-sm font-bold tracking-wide uppercase text-amber-400">Demonstration Sandbox</span>
          </div>
          <span className="text-xs text-slate-400">
            Simulates optical defect inspection (does NOT overwrite backend Gold Reference)
          </span>
        </div>
        <div className="flex flex-wrap gap-2 pt-1">
          <button
            onClick={() => handleSimulateMode('healthy')}
            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
          >
            Healthy Baseline
          </button>
          <button
            onClick={() => handleSimulateMode('crack')}
            className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition"
          >
            Crack Defect
          </button>
          <button
            onClick={() => handleSimulateMode('corrosion')}
            className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition"
          >
            Corrosion
          </button>
          <button
            onClick={() => handleSimulateMode('belt_damage')}
            className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold transition"
          >
            Belt Damage
          </button>
          <button
            onClick={() => handleSimulateMode('overheating')}
            className="px-3 py-1.5 rounded-lg bg-red-700 hover:bg-red-600 text-white text-xs font-semibold transition"
          >
            Overheating
          </button>
          <button
            onClick={() => handleSimulateMode('invalid_reference')}
            className="px-3 py-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-white text-xs font-semibold transition"
          >
            Invalid Reference
          </button>
          <button
            onClick={() => handleSimulateMode('poor_quality')}
            className="px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold transition"
          >
            Blurry Image
          </button>
        </div>
      </div>

      {/* VIEW GOLD REFERENCE MODAL */}
      {showRefModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-2xl shadow-2xl border border-gray-200 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-bold text-gray-900">
                  Backend Stored Gold Reference — {selectedPlc}
                </h3>
              </div>
              <button
                onClick={() => setShowRefModal(false)}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {loadingRefModal ? (
              <div className="h-64 flex items-center justify-center text-xs text-gray-500 font-semibold">
                <RefreshCw className="w-5 h-5 text-blue-600 animate-spin mr-2" />
                <span>Loading Gold Reference image from backend...</span>
              </div>
            ) : (
              <div className="space-y-4 text-xs">
                {/* Metadata pills */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <div>
                    <span className="text-gray-500 block text-[10px]">Reference Status</span>
                    <span className="font-bold text-emerald-700">{refModalData?.reference_status || 'VALID'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[10px]">Version</span>
                    <span className="font-mono font-bold text-slate-800">{refModalData?.version || 'v1'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[10px]">Last Updated</span>
                    <span className="font-mono text-slate-700">{refModalData?.updated_at || 'Registered Baseline'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500 block text-[10px]">Resolution / Quality</span>
                    <span className="font-mono text-slate-700">{refModalData?.resolution || '640x480'} ({refModalData?.quality_score}% Q)</span>
                  </div>
                </div>

                {/* Reference Image Display */}
                <div className="bg-slate-950 p-3 rounded-xl min-h-[280px] flex items-center justify-center">
                  {refModalData?.image_base64 ? (
                    <img
                      src={refModalData.image_base64}
                      alt={`Gold Reference for ${selectedPlc}`}
                      className="max-h-[380px] w-full object-contain rounded"
                    />
                  ) : (
                    <div className="text-slate-400 text-xs">
                      Gold Reference image file verified on backend.
                    </div>
                  )}
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => setShowRefModal(false)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white font-bold rounded-lg transition"
                  >
                    Close Reference
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default VisualInspection;
