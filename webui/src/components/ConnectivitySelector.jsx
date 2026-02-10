import React, { useState } from 'react';

const CONNECTIVITY_OPTIONS = [
  {
    value: 'cloudflare',
    title: 'Cloudflare Tunnel',
    description: 'Easiest option. No port forwarding needed. Paste your Cloudflare Tunnel token.',
    recommended: true,
  },
  {
    value: 'tailscale',
    title: 'Tailscale VPN',
    description: 'Secure mesh network. Requires Tailscale authentication key.',
  },
  {
    value: 'ddns',
    title: 'Dynamic DNS + Port Forward',
    description: 'Traditional approach. Configure your router to forward port 8000.',
  },
  {
    value: 'relay',
    title: 'Cloud Relay',
    description: 'Custom VPS proxy. Requires your own relay server.',
  },
  {
    value: 'none',
    title: 'Local Network Only',
    description: 'No external access. Use only on local network.',
  },
];

function ConnectivitySelector({ selected, onChange }) {
  const [method, setMethod] = useState(selected.method || 'none');
  const [config, setConfig] = useState(selected.config || {});

  const handleMethodChange = (newMethod) => {
    setMethod(newMethod);
    onChange({ method: newMethod, config: {} });
    setConfig({});
  };

  const handleConfigChange = (field, value) => {
    const newConfig = { ...config, [field]: value };
    setConfig(newConfig);
    onChange({ method, config: newConfig });
  };

  const renderConfigFields = () => {
    switch (method) {
      case 'cloudflare':
        return (
          <div className="form-group">
            <label>Cloudflare Tunnel Token</label>
            <input
              type="text"
              placeholder="Paste your tunnel token here..."
              value={config.tunnel_token || ''}
              onChange={(e) => handleConfigChange('tunnel_token', e.target.value)}
            />
            <small style={{ display: 'block', marginTop: '0.5rem', opacity: 0.8 }}>
              Get your token from the Cloudflare Zero Trust dashboard
            </small>
          </div>
        );

      case 'tailscale':
        return (
          <div className="form-group">
            <label>Tailscale Auth Key</label>
            <input
              type="text"
              placeholder="Paste your Tailscale auth key..."
              value={config.auth_key || ''}
              onChange={(e) => handleConfigChange('auth_key', e.target.value)}
            />
            <small style={{ display: 'block', marginTop: '0.5rem', opacity: 0.8 }}>
              Generate an auth key in your Tailscale admin console
            </small>
          </div>
        );

      case 'ddns':
        return (
          <div>
            <div className="form-group">
              <label>Dynamic DNS Hostname</label>
              <input
                type="text"
                placeholder="yourname.ddns.net"
                value={config.hostname || ''}
                onChange={(e) => handleConfigChange('hostname', e.target.value)}
              />
            </div>
            <div className="instructions">
              <h4>Setup Instructions:</h4>
              <ol style={{ marginLeft: '1.5rem', marginTop: '0.5rem' }}>
                <li>Configure your router to forward port 8000 to this device</li>
                <li>Set up a dynamic DNS service (e.g., No-IP, DynDNS)</li>
                <li>Enter your DDNS hostname above</li>
              </ol>
            </div>
          </div>
        );

      case 'relay':
        return (
          <div className="form-group">
            <label>Relay Server URL</label>
            <input
              type="text"
              placeholder="https://relay.yourdomain.com"
              value={config.relay_url || ''}
              onChange={(e) => handleConfigChange('relay_url', e.target.value)}
            />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div>
      <h2>Connectivity Method</h2>
      <p>Choose how Salesforce will connect to your CloudPrintd server:</p>

      <div className="radio-group" style={{ marginTop: '1.5rem' }}>
        {CONNECTIVITY_OPTIONS.map((option) => (
          <label
            key={option.value}
            className={`radio-option ${method === option.value ? 'selected' : ''}`}
          >
            <input
              type="radio"
              name="connectivity"
              value={option.value}
              checked={method === option.value}
              onChange={(e) => handleMethodChange(e.target.value)}
            />
            <div className="radio-content">
              <div className="radio-title">
                {option.title}
                {option.recommended && (
                  <span className="badge success" style={{ marginLeft: '0.5rem' }}>
                    Recommended
                  </span>
                )}
              </div>
              <div className="radio-description">{option.description}</div>
            </div>
          </label>
        ))}
      </div>

      {method !== 'none' && (
        <div style={{ marginTop: '2rem' }}>
          {renderConfigFields()}
        </div>
      )}
    </div>
  );
}

export default ConnectivitySelector;
