import React, { useState, useEffect } from 'react';
import { securityAPI } from '../api';
import './APIKeyManager.css';

const APIKeyManager = () => {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newToken, setNewToken] = useState(null);
  const [showNewToken, setShowNewToken] = useState(false);

  useEffect(() => {
    loadTokens();
  }, []);

  const loadTokens = async () => {
    try {
      const response = await securityAPI.listTokens();
      setTokens(response.data.tokens);
      setError(null);
    } catch (err) {
      console.error('Error loading tokens:', err);
      setError('Failed to load API tokens');
    }
  };

  const handleGenerateToken = async () => {
    if (!confirm('Generate a new API token? Your existing tokens will remain valid.')) {
      return;
    }

    setLoading(true);
    try {
      const response = await securityAPI.regenerateToken();
      setNewToken(response.data.token);
      setShowNewToken(true);
      await loadTokens();
      setError(null);
    } catch (err) {
      console.error('Error generating token:', err);
      setError('Failed to generate new token: ' + (err.response?.data?.message || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteToken = async (tokenIndex, tokenPreview) => {
    if (!confirm(`Delete API token ${tokenPreview}?\n\nThis action cannot be undone. Make sure you're not using this token in production before deleting it.`)) {
      return;
    }

    setLoading(true);
    try {
      await securityAPI.deleteToken(tokenIndex);
      await loadTokens();
      setError(null);
    } catch (err) {
      console.error('Error deleting token:', err);
      const errorMsg = err.response?.data?.detail || err.response?.data?.message || err.message;
      setError('Failed to delete token: ' + errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Token copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy:', err);
      alert('Failed to copy to clipboard. Please copy manually.');
    });
  };

  return (
    <div className="api-key-manager">
      <h2>API Token Management</h2>
      <p className="description">
        Manage API tokens for secure communication between Salesforce and CloudPrintd.
        Each token can be used independently.
      </p>

      {error && <div className="error-message">{error}</div>}

      {showNewToken && newToken && (
        <div className="new-token-panel">
          <div className="new-token-header">
            <h3>⚠️ New Token Generated</h3>
            <button onClick={() => setShowNewToken(false)} className="btn-small">✕</button>
          </div>
          <div className="new-token-content">
            <p className="warning-text">
              <strong>Important:</strong> Copy this token now. You won't be able to see it again!
            </p>
            <div className="token-display">
              <code>{newToken}</code>
              <button onClick={() => copyToClipboard(newToken)} className="btn-copy">
                📋 Copy
              </button>
            </div>
            <div className="salesforce-instructions">
              <h4>Add to Salesforce:</h4>
              <ol>
                <li>Setup → Named Credentials → Your CloudPrintd credential</li>
                <li>Edit the Password field</li>
                <li>Paste this token</li>
                <li>Save</li>
              </ol>
            </div>
          </div>
        </div>
      )}

      <div className="tokens-section">
        <div className="section-header">
          <h3>Active Tokens ({tokens.length})</h3>
          <button 
            onClick={handleGenerateToken} 
            disabled={loading}
            className="btn-primary"
          >
            + Generate New Token
          </button>
        </div>

        {tokens.length === 0 ? (
          <div className="empty-state">
            <p>No API tokens configured.</p>
            <button onClick={handleGenerateToken} disabled={loading} className="btn-primary">
              Generate Your First Token
            </button>
          </div>
        ) : (
          <div className="tokens-list">
            {tokens.map((token) => (
              <div key={token.id} className="token-item">
                <div className="token-info">
                  <div className="token-preview">
                    <code>{token.token}</code>
                  </div>
                  <div className="token-meta">
                    Created: {token.created_at}
                  </div>
                </div>
                <div className="token-actions">
                  {tokens.length > 1 && (
                    <button
                      onClick={() => handleDeleteToken(token.id, token.token)}
                      disabled={loading}
                      className="btn-delete"
                    >
                      🗑️ Delete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="help-section">
          <h4>💡 Token Management Tips:</h4>
          <ul>
            <li>Tokens are used for authentication with the CloudPrintd API</li>
            <li>You can have multiple active tokens for different environments</li>
            <li>Rotateperiodically for better security</li>
            <li>Cannot delete the last token or the token currently in use</li>
            <li>Store tokens securely - treat them like passwords</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default APIKeyManager;
