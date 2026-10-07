import axios from 'axios';

const getBaseURL = () => {
  if (typeof window !== 'undefined') {
    if (window.location.port === '5173' || window.location.port === '3000') {
      return 'http://127.0.0.1:8000/api';
    }
  }
  return '/api';
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getStatus = async () => {
  try {
    const res = await api.get('/status');
    return res.data;
  } catch (err) {
    console.error('API Error (getStatus):', err.message);
    throw err;
  }
};

export const getPlcsData = async () => {
  try {
    const res = await api.get('/plcs');
    return res.data;
  } catch (err) {
    console.error('API Error (getPlcsData):', err.message);
    throw err;
  }
};

export const getCurrentData = async (plc_id = 'PLC_01') => {
  try {
    const res = await api.get('/current', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getCurrentData):', err.message);
    throw err;
  }
};

export const getTagsData = async (plc_id = 'PLC_01') => {
  try {
    const res = await api.get('/tags', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getTagsData):', err.message);
    throw err;
  }
};

export const getHistoryData = async (plc_id = 'PLC_01', tag = 'Motor_Temp') => {
  try {
    const res = await api.get('/history', { params: { plc_id, tag } });
    return res.data;
  } catch (err) {
    console.error('API Error (getHistoryData):', err.message);
    throw err;
  }
};

export const getModelMetrics = async () => {
  try {
    const res = await api.get('/model', { timeout: 10000 });
    return res.data;
  } catch (err) {
    console.warn('Model metrics endpoint unavailable or timed out, returning fallback metrics:', err.message);
    return {
      isFallback: true,
      mae: 8.42,
      rmse: 11.15,
      r2_score: 0.982,
      dataset_size: 91250,
      feature_importance: { Temperature: 0.48, Vibration: 0.35, Motor_Current: 0.17 },
      residual_plot_data: []
    };
  }
};

export const getRecentLogs = async (plc_id = null) => {
  try {
    const params = plc_id ? { plc_id } : {};
    const res = await api.get('/logs', { params });
    return res.data;
  } catch (err) {
    console.error('API Error (getRecentLogs):', err.message);
    throw err;
  }
};

export const getMaintenanceData = async (plc_id = 1) => {
  try {
    const res = await api.get('/maintenance', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getMaintenanceData):', err.message);
    throw err;
  }
};

export const postControlAction = async (action, speed = 1.0) => {
  try {
    const res = await api.post('/control', { action, speed });
    return res.data;
  } catch (err) {
    console.error(`API Error (postControlAction '${action}'):`, err.message);
    throw err;
  }
};

export const getMlMetrics = async () => {
  try {
    const res = await api.get('/ml/metrics');
    return res.data;
  } catch (err) {
    console.warn('API Error (getMlMetrics):', err.message);
    return null;
  }
};

export const getFeaturesSummary = async () => {
  try {
    const res = await api.get('/features/summary');
    return res.data;
  } catch (err) {
    console.warn('API Error (getFeaturesSummary):', err.message);
    return null;
  }
};

// =====================================================================
// DATA & MODEL DRIFT MONITORING API METHODS
// =====================================================================

export const getDriftSummary = async (plc_id = 'PLC_01') => {
  try {
    const res = await api.get('/drift/summary', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getDriftSummary):', err.message);
    throw err;
  }
};

export const getDriftFeatures = async (plc_id = 'PLC_01') => {
  try {
    const res = await api.get('/drift/features', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getDriftFeatures):', err.message);
    throw err;
  }
};

export const getDriftPredictions = async (plc_id = 'PLC_01') => {
  try {
    const res = await api.get('/drift/predictions', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getDriftPredictions):', err.message);
    throw err;
  }
};

export const getDriftQuality = async (plc_id = 'PLC_01') => {
  try {
    const res = await api.get('/drift/data-quality', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getDriftQuality):', err.message);
    throw err;
  }
};

export const getDriftHistory = async (plc_id = 'PLC_01', limit = 40) => {
  try {
    const res = await api.get('/drift/history', { params: { plc_id, limit } });
    return res.data;
  } catch (err) {
    console.error('API Error (getDriftHistory):', err.message);
    throw err;
  }
};

export const getDriftAlerts = async (plc_id = null, limit = 30) => {
  try {
    const params = plc_id ? { plc_id, limit } : { limit };
    const res = await api.get('/drift/alerts', { params });
    return res.data;
  } catch (err) {
    console.error('API Error (getDriftAlerts):', err.message);
    throw err;
  }
};

export const getDriftBaseline = async () => {
  try {
    const res = await api.get('/drift/baseline');
    return res.data;
  } catch (err) {
    console.error('API Error (getDriftBaseline):', err.message);
    throw err;
  }
};

export const postRebuildBaseline = async () => {
  try {
    const res = await api.post('/drift/baseline/rebuild');
    return res.data;
  } catch (err) {
    console.error('API Error (postRebuildBaseline):', err.message);
    throw err;
  }
};

export const postSimulateDrift = async (plc_id = 'PLC_01', mode = 'normal') => {
  try {
    const res = await api.post('/drift/simulate-drift', { plc_id, mode });
    return res.data;
  } catch (err) {
    console.error(`API Error (postSimulateDrift '${mode}'):`, err.message);
    throw err;
  }
};

export const postTriggerDriftCheck = async (plc_id = 'PLC_01') => {
  try {
    const res = await api.post('/drift/check', null, { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (postTriggerDriftCheck):', err.message);
    throw err;
  }
};

// =====================================================================
// ASSET DIGITAL THREAD API METHODS
// =====================================================================

export const getAssets = async () => {
  try {
    const res = await api.get('/assets');
    return res.data;
  } catch (err) {
    console.error('API Error (getAssets):', err.message);
    throw err;
  }
};

export const getAssetDetails = async (asset_id) => {
  try {
    const res = await api.get(`/assets/${encodeURIComponent(asset_id)}`);
    return res.data;
  } catch (err) {
    console.error(`API Error (getAssetDetails ${asset_id}):`, err.message);
    throw err;
  }
};

export const getAssetComponents = async (asset_id) => {
  try {
    const res = await api.get(`/assets/${encodeURIComponent(asset_id)}/components`);
    return res.data;
  } catch (err) {
    console.error(`API Error (getAssetComponents ${asset_id}):`, err.message);
    throw err;
  }
};

export const getAssetSensors = async (asset_id) => {
  try {
    const res = await api.get(`/assets/${encodeURIComponent(asset_id)}/sensors`);
    return res.data;
  } catch (err) {
    console.error(`API Error (getAssetSensors ${asset_id}):`, err.message);
    throw err;
  }
};

export const getAssetHealth = async (asset_id) => {
  try {
    const res = await api.get(`/assets/${encodeURIComponent(asset_id)}/health`);
    return res.data;
  } catch (err) {
    console.error(`API Error (getAssetHealth ${asset_id}):`, err.message);
    throw err;
  }
};

export const getAssetTimeline = async (asset_id, event_type = null, severity = null, limit = 100) => {
  try {
    const params = { limit };
    if (event_type && event_type !== 'ALL') params.event_type = event_type;
    if (severity && severity !== 'ALL') params.severity = severity;
    const res = await api.get(`/assets/${encodeURIComponent(asset_id)}/timeline`, { params });
    return res.data;
  } catch (err) {
    console.error(`API Error (getAssetTimeline ${asset_id}):`, err.message);
    throw err;
  }
};

export const getAssetMaintenance = async (asset_id) => {
  try {
    const res = await api.get(`/assets/${encodeURIComponent(asset_id)}/maintenance`);
    return res.data;
  } catch (err) {
    console.error(`API Error (getAssetMaintenance ${asset_id}):`, err.message);
    throw err;
  }
};

export const postAssetMaintenance = async (asset_id, maintenanceData) => {
  try {
    const res = await api.post(`/assets/${encodeURIComponent(asset_id)}/maintenance`, maintenanceData);
    return res.data;
  } catch (err) {
    console.error(`API Error (postAssetMaintenance ${asset_id}):`, err.message);
    throw err;
  }
};

export const postAssetMaintenanceOutcome = async (asset_id, maintenance_id, outcomeData) => {
  try {
    const res = await api.post(`/assets/${encodeURIComponent(asset_id)}/maintenance/${encodeURIComponent(maintenance_id)}/outcome`, outcomeData);
    return res.data;
  } catch (err) {
    console.error(`API Error (postAssetMaintenanceOutcome ${maintenance_id}):`, err.message);
    throw err;
  }
};

// =====================================================================
// YOLO11 VISUAL HEALTH & GOLD REFERENCE API ENDPOINTS
// =====================================================================

export const getVisualInspectionResult = async (plc_id = 'PLC_01') => {
  try {
    const res = await api.get(`/visual-inspection/result/${encodeURIComponent(plc_id)}`);
    return res.data;
  } catch (err) {
    console.error(`API Error (getVisualInspectionResult ${plc_id}):`, err.message);
    throw err;
  }
};

export const getVisualReference = async (plc_id = 'PLC_01', include_image = false) => {
  try {
    const res = await api.get(`/visual-inspection/reference/${encodeURIComponent(plc_id)}`, {
      params: { include_image }
    });
    return res.data;
  } catch (err) {
    console.error(`API Error (getVisualReference ${plc_id}):`, err.message);
    throw err;
  }
};

export const getVisualHistory = async (plc_id = 'PLC_01', limit = 30) => {
  try {
    const res = await api.get(`/visual-inspection/history/${encodeURIComponent(plc_id)}`, { params: { limit } });
    return res.data;
  } catch (err) {
    console.error(`API Error (getVisualHistory ${plc_id}):`, err.message);
    throw err;
  }
};

export const analyzeVisualImage = async (plc_id = 'PLC_01', image_base64 = null) => {
  try {
    const res = await api.post('/visual-inspection/analyze', { plc_id, image_base64 });
    return res.data;
  } catch (err) {
    console.error(`API Error (analyzeVisualImage ${plc_id}):`, err.message);
    throw err;
  }
};

export const setVisualReference = async (plc_id = 'PLC_01', image_base64) => {
  try {
    const res = await api.post('/visual-inspection/reference', { plc_id, image_base64 });
    return res.data;
  } catch (err) {
    console.error(`API Error (setVisualReference ${plc_id}):`, err.message);
    throw err;
  }
};

export const simulateVisualDefect = async (plc_id = 'PLC_01', mode = 'crack') => {
  try {
    const res = await api.post('/visual-inspection/simulate-defect', { plc_id, mode });
    return res.data;
  } catch (err) {
    console.error(`API Error (simulateVisualDefect ${plc_id} ${mode}):`, err.message);
    throw err;
  }
};

// =====================================================================
// ACTUAL VS PREDICTED & MAINTENANCE HISTORY GRAPH API ENDPOINTS
// =====================================================================

export const getActualVsPredictedData = async () => {
  try {
    const res = await api.get('/analytics/actual-vs-predicted');
    return res.data;
  } catch (err) {
    console.error('API Error (getActualVsPredictedData):', err.message);
    throw err;
  }
};

export const getMaintenanceHistoryData = async (plc_id = 'PLC_01', limit = 100) => {
  try {
    const res = await api.get('/maintenance/history', { params: { plc_id, limit } });
    return res.data;
  } catch (err) {
    console.error(`API Error (getMaintenanceHistoryData ${plc_id}):`, err.message);
    throw err;
  }
};

// =====================================================================
// MAINTENANCE COST OPTIMIZATION & ENERGY-AWARE PREDICTIVE MAINTENANCE
// =====================================================================

export const getCostConfig = async () => {
  try {
    const res = await api.get('/cost-config');
    return res.data;
  } catch (err) {
    console.error('API Error (getCostConfig):', err.message);
    throw err;
  }
};

export const postCostConfig = async (config) => {
  try {
    const res = await api.post('/cost-config', config);
    return res.data;
  } catch (err) {
    console.error('API Error (postCostConfig):', err.message);
    throw err;
  }
};

export const postAddPlc = async (plc_id, options = {}) => {
  try {
    const res = await api.post('/plcs/add', { plc_id, ...options });
    return res.data;
  } catch (err) {
    console.error(`API Error (postAddPlc ${plc_id}):`, err.message);
    throw err;
  }
};

export const getMaintenanceOverview = async () => {
  try {
    const res = await api.get('/maintenance/overview');
    return res.data;
  } catch (err) {
    console.error('API Error (getMaintenanceOverview):', err.message);
    throw err;
  }
};

export const getEnergyData = async (plc_id = 'PLC_01') => {
  try {
    const res = await api.get('/energy', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error(`API Error (getEnergyData ${plc_id}):`, err.message);
    throw err;
  }
};






