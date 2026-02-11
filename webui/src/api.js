import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('api_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// API methods
export const setupAPI = {
  getStatus: () => api.get('/setup/status'),
  generateToken: () => api.post('/setup/token'),
  complete: () => api.post('/setup/complete'),
};

export const printersAPI = {
  list: () => api.get('/printers'),
  add: (printerId, config) => api.post('/printers', { id: printerId, config }),
  update: (printerId, config) => api.put(`/printers/${printerId}`, { config }),
  remove: (printerId) => api.delete(`/printers/${printerId}`),
  discover: (ipRange = '192.168.1.0/24') => api.post('/discover', null, { params: { ip_range: ipRange } }),
};

export const printAPI = {
  submit: (printJob) => api.post('/print', printJob),
  stats: () => api.get('/stats'),
  test: (printerId, content, format = 'zpl') => api.post('/print', {
    printer: printerId,
    content: content,
    format: format,
    copies: 1
  }),
};

export const systemAPI = {
  health: () => api.get('/health'),
  version: () => api.get('/system/version'),
  versions: () => api.get('/system/versions'),
  update: (version) => api.post(`/system/update/${version}`),
  rollback: () => api.post('/system/rollback'),
  changelog: (version) => api.get(`/system/changelog/${version}`),
  getUpdateConfig: () => api.get('/system/update-config'),
  updateUpdateConfig: (config) => api.put('/system/update-config', config),
  
  // Service control
  serviceStatus: () => api.get('/system/service/status'),
  restartService: () => api.post('/system/service/restart'),
  serviceLogs: (lines = 100) => api.get('/system/service/logs', { params: { lines } }),
};

export const securityAPI = {
  regenerateToken: () => api.post('/security/token/regenerate'),
  listTokens: () => api.get('/security/tokens'),
  deleteToken: (tokenIndex) => api.delete(`/security/token/${tokenIndex}`),
};

export const networkAPI = {
  status: () => api.get('/network/status'),
  scan: () => api.get('/network/scan'),
  configure: (ssid, password, hidden = false) => 
    api.post('/network/wifi/configure', { ssid, password, hidden }),
  reset: () => api.post('/network/wifi/reset'),
  getHostname: () => api.get('/network/hostname'),
  setHostname: (hostname) => api.post('/network/hostname', null, { params: { hostname } }),
};

export default api;
