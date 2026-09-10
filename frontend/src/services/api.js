import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
});

export const getStatus = async () => {
  const res = await api.get('/status');
  return res.data;
};

export const getPlcsData = async () => {
  const res = await api.get('/plcs');
  return res.data;
};

export const getCurrentData = async (plc_id = 1) => {
  const res = await api.get('/current', { params: { plc_id } });
  return res.data;
};

export const getHistoryData = async () => {
  const res = await api.get('/history');
  return res.data;
};

export const getModelMetrics = async () => {
  try {
    const res = await api.get('/model', { timeout: 15000 });
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
  const params = plc_id ? { plc_id } : {};
  const res = await api.get('/logs', { params });
  return res.data;
};

export const getMaintenanceData = async (plc_id = 1) => {
  const res = await api.get('/maintenance', { params: { plc_id } });
  return res.data;
};

export const postControlAction = async (action, speed = 1.0) => {
  const res = await api.post('/control', { action, speed });
  return res.data;
};
