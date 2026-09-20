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

export const getCurrentData = async (plc_id = 1) => {
  try {
    const res = await api.get('/current', { params: { plc_id } });
    return res.data;
  } catch (err) {
    console.error('API Error (getCurrentData):', err.message);
    throw err;
  }
};

export const getHistoryData = async (plc_id = 1) => {
  try {
    const res = await api.get('/history', { params: { plc_id } });
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
