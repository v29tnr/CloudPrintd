import React, { useState } from 'react';
import { systemAPI } from '../api';

function VersionCard({ version, isCurrent, onUpdate }) {
  const [showChangelog, setShowChangelog] = useState(false);
  const [changelog, setChangelog] = useState(null);
  const [loadingChangelog, setLoadingChangelog] = useState(false);

  const loadChangelog = async () => {
    if (changelog) {
      setShowChangelog(!showChangelog);
      return;
    }

    setLoadingChangelog(true);
    try {
      const response = await systemAPI.changelog(version.version);
      setChangelog(response.data.changelog);
      setShowChangelog(true);
    } catch (err) {
      setChangelog('Changelog not available');
      setShowChangelog(true);
    } finally {
      setLoadingChangelog(false);
    }
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getActionButton = () => {
    if (isCurrent) {
      return (
        <span className="badge success">CURRENT</span>
      );
    }

    if (version.is_installed) {
      return (
        <button
          onClick={() => onUpdate(version.version)}
          className="primary"
        >
          Activate
        </button>
      );
    }

    return (
      <button
        onClick={() => onUpdate(version.version)}
        className="secondary"
      >
        Download & Install
      </button>
    );
  };

  return (
    <div className="version-card">
      <div className="version-header">
        <div className="version-title">
          <h3 style={{ margin: 0 }}>v{version.version}</h3>
          {isCurrent && <span className="badge success">CURRENT</span>}
          {version.is_installed && !isCurrent && (
            <span className="badge info">INSTALLED</span>
          )}
          {!version.is_installed && <span className="badge warning">AVAILABLE</span>}
        </div>
        <div className="version-actions">
          {getActionButton()}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.5rem', fontSize: '0.875rem', opacity: 0.8 }}>
        <div>
          <strong>Channel:</strong> {version.channel}
        </div>
        <div>
          <strong>Released:</strong> {formatDate(version.release_date)}
        </div>
        {version.size_bytes > 0 && (
          <div>
            <strong>Size:</strong> {formatSize(version.size_bytes)}
          </div>
        )}
      </div>

      {version.changelog || true ? (
        <div className="changelog">
          <button
            onClick={loadChangelog}
            className="changelog-toggle"
            disabled={loadingChangelog}
          >
            {loadingChangelog
              ? 'Loading...'
              : showChangelog
              ? '▼ Hide Changelog'
              : '▶ Show Changelog'
            }
          </button>
          {showChangelog && changelog && (
            <div className="changelog-content">
              {changelog}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

export default VersionCard;
