import React, { useState, useEffect } from 'react';
import { systemAPI } from '../api';
import VersionCard from './VersionCard';

function UpdateManager() {
  const [versions, setVersions] = useState([]);
  const [currentVersion, setCurrentVersion] = useState(null);
  const [updateConfig, setUpdateConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    loadVersions();
    loadUpdateConfig();
  }, []);

  const loadVersions = async () => {
    setLoading(true);
    setError(null);

    try {
      const [versionsRes, currentRes] = await Promise.all([
        systemAPI.versions(),
        systemAPI.version(),
      ]);

      setVersions(versionsRes.data);
      setCurrentVersion(currentRes.data.current_version);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load versions');
    } finally {
      setLoading(false);
    }
  };

  const loadUpdateConfig = async () => {
    try {
      const response = await systemAPI.getUpdateConfig();
      setUpdateConfig(response.data);
    } catch (err) {
      console.error('Failed to load update config:', err);
    }
  };

  const checkForUpdates = async () => {
    setChecking(true);
    setError(null);
    setSuccess(null);

    try {
      await loadVersions();
      setSuccess('Version list refreshed');
    } catch (err) {
      setError('Failed to check for updates');
    } finally {
      setChecking(false);
    }
  };

  const handleUpdate = async (version) => {
    setError(null);
    setSuccess(null);

    try {
      await systemAPI.update(version);
      setSuccess(`Update to version ${version} started. This may take a few minutes.`);
      
      // Refresh after a delay
      setTimeout(loadVersions, 5000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to start update');
    }
  };

  const handleRollback = async () => {
    if (!confirm('Are you sure you want to rollback to the previous version?')) {
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      const response = await systemAPI.rollback();
      setSuccess(response.data.message);
      
      // Refresh after a delay
      setTimeout(loadVersions, 5000);
    } catch (err) {
      setError(err.response?.data?.message || 'Rollback failed');
    }
  };

  const updateSettings = async (newConfig) => {
    try {
      await systemAPI.updateUpdateConfig(newConfig);
      setUpdateConfig(newConfig);
      setSuccess('Update settings saved');
    } catch (err) {
      setError('Failed to save settings');
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <h2>Loading versions...</h2>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2>Version Management</h2>
          <p style={{ opacity: 0.8, marginTop: '0.5rem' }}>
            Current version: <strong>{currentVersion || 'Unknown'}</strong>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            onClick={checkForUpdates}
            disabled={checking}
            className="secondary"
          >
            {checking ? 'Checking...' : 'Check for Updates'}
          </button>
          <button
            onClick={handleRollback}
            className="danger"
          >
            Rollback to Previous
          </button>
        </div>
      </div>

      {error && (
        <div className="error">{error}</div>
      )}

      {success && (
        <div className="success-message">{success}</div>
      )}

      {updateConfig && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h3>Update Settings</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={updateConfig.auto_update}
                  onChange={(e) => updateSettings({ ...updateConfig, auto_update: e.target.checked })}
                  style={{ width: 'auto', marginRight: '0.5rem' }}
                />
                Enable automatic updates
              </label>
            </div>

            <div className="form-group">
              <label>Release Channel</label>
              <select
                value={updateConfig.channel}
                onChange={(e) => updateSettings({ ...updateConfig, channel: e.target.value })}
              >
                <option value="stable">Stable</option>
                <option value="beta">Beta</option>
                <option value="dev">Development</option>
              </select>
            </div>

            <div className="form-group">
              <label>Keep Previous Versions</label>
              <input
                type="number"
                min="1"
                max="5"
                value={updateConfig.keep_previous_versions}
                onChange={(e) => updateSettings({ 
                  ...updateConfig, 
                  keep_previous_versions: parseInt(e.target.value) 
                })}
              />
            </div>
          </div>
        </div>
      )}

      <h3>Available Versions</h3>
      {versions.length > 0 ? (
        <div className="version-list">
          {versions.map((version) => (
            <VersionCard
              key={version.version}
              version={version}
              isCurrent={version.version === currentVersion}
              onUpdate={handleUpdate}
            />
          ))}
        </div>
      ) : (
        <p style={{ opacity: 0.8, marginTop: '1rem' }}>
          No versions available. Check your update server configuration.
        </p>
      )}
    </div>
  );
}

export default UpdateManager;
