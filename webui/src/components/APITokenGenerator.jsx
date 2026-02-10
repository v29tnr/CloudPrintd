import React, { useState } from 'react';
import { setupAPI } from '../api';

function APITokenGenerator({ token, onTokenGenerated }) {
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  const generateToken = async () => {
    setGenerating(true);
    setError(null);

    try {
      const response = await setupAPI.generateToken();
      const newToken = response.data.token;
      
      // Store token in localStorage
      localStorage.setItem('api_token', newToken);
      
      onTokenGenerated(newToken);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to generate token');
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = () => {
    if (token) {
      navigator.clipboard.writeText(token);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div>
      <h2>API Security</h2>
      <p>Generate an API token to secure communication between Salesforce and CloudPrintd:</p>

      <div style={{ marginTop: '1.5rem' }}>
        {!token ? (
          <button
            onClick={generateToken}
            disabled={generating}
            className="primary"
            style={{ width: '100%', padding: '1rem' }}
          >
            {generating ? 'Generating...' : 'Generate API Token'}
          </button>
        ) : (
          <div>
            <div className="token-display">
              <div style={{ marginBottom: '0.5rem', fontWeight: 'bold' }}>
                Your API Token:
              </div>
              <div style={{ wordBreak: 'break-all', fontSize: '0.9rem' }}>
                {token}
              </div>
              <button
                onClick={copyToClipboard}
                className="secondary copy-button"
              >
                {copied ? 'Copied! ✓' : 'Copy Token'}
              </button>
            </div>

            <div className="instructions" style={{ marginTop: '1.5rem' }}>
              <h4>Salesforce Integration Instructions:</h4>
              <ol style={{ marginLeft: '1.5rem', marginTop: '0.5rem' }}>
                <li>
                  <strong>Create a Named Credential in Salesforce:</strong>
                  <ul style={{ marginLeft: '1rem', marginTop: '0.25rem' }}>
                    <li>Setup → Named Credentials → New Named Credential</li>
                    <li>Label: <code>CloudPrintd_Server</code></li>
                    <li>URL: Your CloudPrintd server URL</li>
                    <li>Authentication Protocol: Password Authentication</li>
                    <li>Username: <code>api</code> (any value)</li>
                    <li>Password: Paste the token above</li>
                  </ul>
                </li>
                <li style={{ marginTop: '0.5rem' }}>
                  <strong>Use in Apex:</strong>
                  <pre style={{
                    backgroundColor: 'rgba(0,0,0,0.3)',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    marginTop: '0.25rem',
                    overflow: 'auto'
                  }}>
{`HttpRequest req = new HttpRequest();
req.setEndpoint('callout:CloudPrintd_Server/api/v1/print');
req.setMethod('POST');
req.setHeader('Authorization', 'Bearer ' + apiToken);
req.setHeader('Content-Type', 'application/json');
req.setBody(JSON.serialize(printJob));
Http http = new Http();
HttpResponse res = http.send(req);`}
                  </pre>
                </li>
                <li style={{ marginTop: '0.5rem' }}>
                  <strong>Optional:</strong> Enable IP whitelisting and add Salesforce IPs:
                  <ul style={{ marginLeft: '1rem', marginTop: '0.25rem' }}>
                    <li>13.110.54.0/24</li>
                    <li>13.108.0.0/14</li>
                    <li>And other Salesforce IP ranges for your instance</li>
                  </ul>
                </li>
              </ol>
            </div>

            <div className="card" style={{ marginTop: '1.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
              <h4 style={{ color: '#ef4444' }}>⚠️ Important Security Notes:</h4>
              <ul style={{ marginLeft: '1.5rem', marginTop: '0.5rem' }}>
                <li>Store this token securely - it provides full access to your print server</li>
                <li>Never commit the token to version control</li>
                <li>You can generate additional tokens later if needed</li>
                <li>Revoke compromised tokens immediately</li>
              </ul>
            </div>
          </div>
        )}

        {error && (
          <div className="error" style={{ marginTop: '1rem' }}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

export default APITokenGenerator;
