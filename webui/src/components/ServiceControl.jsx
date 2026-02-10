import React, { useState, useEffect } from 'react';
import { systemAPI } from '../api';
import './ServiceControl.css';

const ServiceControl = () => {
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const response = await systemAPI.serviceStatus();
      setStatus(response.data);
      setError(null);
    } catch (err) {
      console.error('Error loading service status:', err);
      setError('Failed to load service status');
    }
  };

  const loadLogs = async () => {
    setLoading(true);
    try {
      const response = await systemAPI.serviceLogs(200);
      setLogs(response.data.logs);
      setShowLogs(true);
      setError(null);
    } catch (err) {
      console.error('Error loading logs:', err);
      setError('Failed to load service logs');
    } finally {
      setLoading(false);
    }
  };

  const handleRestart = async () => {
    if (!confirm('Are you sure you want to restart the service? This will interrupt any ongoing operations.')) {
      return;
    }

    setLoading(true);
    try {
      await systemAPI.restartService();
      alert('Restart command issued. The service will restart shortly. Please wait a moment and refresh the page.');
      // Wait a bit then reload status
      setTimeout(() => {
        loadStatus();
        setLoading(false);
      }, 5000);
    } catch (err) {
      console.error('Error restarting service:', err);
      setError('Failed to restart service: ' + (err.response?.data?.message || err.message));
      setLoading(false);
    }
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  return (
    <div className="service-control">
      <h2>Service Control</h2>

      {error && <div className="error-message">{error}</div>}

      {status && (
        <div className="status-panel">
          <div className="status-grid">
            <div className="status-item">
              <label>Status:</label>
              <span className={`status-badge ${status.systemd_status}`}>
                {status.systemd_status || status.status}
              </span>
            </div>
            
            <div className="status-item">
              <label>Version:</label>
              <span>{status.version}</span>
            </div>
            
            <div className="status-item">
              <label>Uptime:</label>
              <span>{formatUptime(status.uptime_seconds)}</span>
            </div>
          </div>

          <div className="action-buttons">
            <button 
              onClick={loadStatus} 
              disabled={loading}
              className="btn-secondary"
            >
              ↻ Refresh Status
            </button>
            
            <button 
              onClick={loadLogs} 
              disabled={loading}
              className="btn-secondary"
            >
              📋 View Logs
            </button>
            
            <button 
              onClick={handleRestart} 
              disabled={loading}
              className="btn-danger"
            >
              ⟳ Restart Service
            </button>
          </div>
        </div>
      )}

      {showLogs && (
        <div className="logs-panel">
          <div className="logs-header">
            <h3>Service Logs (last 200 lines)</h3>
            <button onClick={() => setShowLogs(false)} className="btn-small">✕ Close</button>
          </div>
          <div className="logs-content">
            <pre>
              {logs.join('\n')}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default ServiceControl;
