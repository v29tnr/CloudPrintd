import React, { useState, useEffect } from 'react';
import { systemAPI } from '../api';
import UpdateManager from './UpdateManager';
import ServiceControl from './ServiceControl';
import APIKeyManager from './APIKeyManager';
import NetworkSetup from './NetworkSetup';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadDashboardData();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [healthRes, statsRes] = await Promise.all([
        systemAPI.health(),
        systemAPI.version(),
      ]);
      
      setHealth(healthRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <h2>Loading dashboard...</h2>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="container">
          <h1>CloudPrintd Dashboard</h1>
          <div style={{ marginTop: '0.5rem', opacity: 0.8 }}>
            Version: <strong>{health?.version || 'Unknown'}</strong>
            <span className="badge success" style={{ marginLeft: '1rem' }}>
              {health?.status || 'Unknown'}
            </span>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid #333', overflowX: 'auto' }}>
            <button
              onClick={() => setActiveTab('overview')}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'overview' ? '2px solid #646cff' : 'none',
                padding: '1rem',
                cursor: 'pointer',
                color: activeTab === 'overview' ? '#646cff' : 'inherit',
                whiteSpace: 'nowrap',
              }}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('service')}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'service' ? '2px solid #646cff' : 'none',
                padding: '1rem',
                cursor: 'pointer',
                color: activeTab === 'service' ? '#646cff' : 'inherit',
                whiteSpace: 'nowrap',
              }}
            >
              Service Control
            </button>
            <button
              onClick={() => setActiveTab('apikeys')}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'apikeys' ? '2px solid #646cff' : 'none',
                padding: '1rem',
                cursor: 'pointer',
                color: activeTab === 'apikeys' ? '#646cff' : 'inherit',
                whiteSpace: 'nowrap',
              }}
            >
              API Keys
            </button>
            <button
              onClick={() => setActiveTab('network')}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'network' ? '2px solid #646cff' : 'none',
                padding: '1rem',
                cursor: 'pointer',
                color: activeTab === 'network' ? '#646cff' : 'inherit',
                whiteSpace: 'nowrap',
              }}
            >
              Network
            </button>
            <button
              onClick={() => setActiveTab('updates')}
              style={{
                background: 'none',
                border: 'none',
                borderBottom: activeTab === 'updates' ? '2px solid #646cff' : 'none',
                padding: '1rem',
                cursor: 'pointer',
                color: activeTab === 'updates' ? '#646cff' : 'inherit',
                whiteSpace: 'nowrap',
              }}
            >
              Updates
            </button>
          </div>
        </div>

        {activeTab === 'overview' && (
          <div>
            <div className="dashboard-grid">
              <div className="stat-card">
                <div className="stat-label">System Status</div>
                <div className="stat-value">{health?.status || 'Unknown'}</div>
                <div style={{ fontSize: '0.875rem', opacity: 0.8 }}>
                  Uptime: {health?.uptime_seconds 
                    ? Math.floor(health.uptime_seconds / 3600) + 'h'
                    : 'Unknown'}
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Printers Configured</div>
                <div className="stat-value">{health?.printers_configured || 0}</div>
                <div style={{ fontSize: '0.875rem', opacity: 0.8 }}>
                  Online: {health?.printers_online || 0}
                </div>
              </div>

              <div className="stat-card">
                <div className="stat-label">Current Version</div>
                <div className="stat-value" style={{ fontSize: '1.5rem' }}>
                  {stats?.current_version || 'Unknown'}
                </div>
                <div style={{ fontSize: '0.875rem', opacity: 0.8 }}>
                  Channel: {stats?.channel || 'stable'}
                </div>
              </div>
            </div>

            <div className="card">
              <h2>Quick Actions</h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                <button className="primary" onClick={() => window.location.href = '/setup'}>
                  Run Setup Wizard
                </button>
                <button className="secondary" onClick={() => window.location.href = '/docs'}>
                  View Documentation
                </button>
                <button className="secondary" onClick={loadDashboardData}>
                  Refresh Dashboard
                </button>
              </div>
            </div>

            <div className="card">
              <h2>Getting Started</h2>
              <div style={{ marginTop: '1rem' }}>
                <h3>Test Your Print Server</h3>
                <p style={{ marginTop: '0.5rem', opacity: 0.9 }}>
                  Send a test print job using this curl command:
                </p>
                <pre style={{
                  backgroundColor: 'rgba(0,0,0,0.3)',
                  padding: '1rem',
                  borderRadius: '4px',
                  marginTop: '0.5rem',
                  overflow: 'auto',
                  fontSize: '0.875rem'
                }}>
{`curl -X POST http://localhost:8000/api/v1/print \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "printer": "warehouse_zebra",
    "content": "^XA^FO50,50^A0N,50,50^FDTest Label^FS^XZ",
    "format": "zpl",
    "copies": 1
  }'`}
                </pre>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'service' && (
          <ServiceControl />
        )}

        {activeTab === 'apikeys' && (
          <APIKeyManager />
        )}

        {activeTab === 'network' && (
          <NetworkSetup />
        )}

        {activeTab === 'updates' && (
          <UpdateManager />
        )}
      </div>
    </div>
  );
}

export default Dashboard;
