import React, { useState, useEffect } from 'react';
import { printersAPI } from '../api';

function PrinterDiscovery({ printers, onChange }) {
  const [discovering, setDiscovering] = useState(false);
  const [discovered, setDiscovered] = useState([]);
  const [error, setError] = useState(null);
  const [ipRange, setIpRange] = useState('192.168.1.0/24');
  const [showManualAdd, setShowManualAdd] = useState(false);
  const [manualPrinter, setManualPrinter] = useState({
    id: '',
    type: 'zebra_raw',
    display_name: '',
    ip: '',
    port: 9100,
    location: '',
  });

  useEffect(() => {
    // Load existing printers
    loadPrinters();
  }, []);

  const loadPrinters = async () => {
    try {
      const response = await printersAPI.list();
      onChange(response.data);
    } catch (err) {
      console.error('Failed to load printers:', err);
    }
  };

  const discoverPrinters = async () => {
    setDiscovering(true);
    setError(null);

    try {
      const response = await printersAPI.discover(ipRange);
      setDiscovered(response.data);
      
      if (response.data.length === 0) {
        setError('No printers found on this network. Try a different IP range or add manually.');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Discovery failed');
    } finally {
      setDiscovering(false);
    }
  };

  const addPrinter = async (printerConfig) => {
    try {
      await printersAPI.add(printerConfig.id, {
        type: printerConfig.type,
        display_name: printerConfig.display_name,
        ip: printerConfig.ip,
        port: printerConfig.port,
        location: printerConfig.location,
      });
      
      await loadPrinters();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to add printer');
    }
  };

  const addDiscoveredPrinter = (printer) => {
    const printerConfig = {
      id: `zebra_${printer.ip.replace(/\./g, '_')}`,
      type: 'zebra_raw',
      display_name: `Zebra Printer ${printer.ip}`,
      ip: printer.ip,
      port: printer.port,
      location: '',
    };
    
    addPrinter(printerConfig);
  };

  const addManualPrinter = () => {
    if (!manualPrinter.id || !manualPrinter.display_name) {
      setError('Please fill in printer ID and name');
      return;
    }

    if (manualPrinter.type === 'zebra_raw' && !manualPrinter.ip) {
      setError('IP address is required for raw TCP printers');
      return;
    }

    addPrinter(manualPrinter);
    setManualPrinter({
      id: '',
      type: 'zebra_raw',
      display_name: '',
      ip: '',
      port: 9100,
      location: '',
    });
    setShowManualAdd(false);
  };

  const removePrinter = async (printerId) => {
    try {
      await printersAPI.remove(printerId);
      await loadPrinters();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to remove printer');
    }
  };

  return (
    <div>
      <h2>Printer Discovery</h2>
      <p>Scan your network for printers or add them manually:</p>

      <div className="form-group" style={{ marginTop: '1.5rem' }}>
        <label>IP Range to Scan (CIDR notation)</label>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <input
            type="text"
            value={ipRange}
            onChange={(e) => setIpRange(e.target.value)}
            placeholder="192.168.1.0/24"
            style={{ flex: 1 }}
          />
          <button
            onClick={discoverPrinters}
            disabled={discovering}
            className="primary"
          >
            {discovering ? 'Scanning...' : 'Scan Network'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error">{error}</div>
      )}

      {discovered.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Discovered Printers</h3>
          <div className="printer-grid">
            {discovered.map((printer, idx) => (
              <div key={idx} className="printer-card online">
                <div className="printer-header">
                  <div>
                    <strong>Zebra Printer</strong>
                    <div style={{ fontSize: '0.875rem', opacity: 0.8 }}>
                      {printer.ip}:{printer.port}
                    </div>
                  </div>
                  <span className="badge success">Found</span>
                </div>
                <div className="printer-actions">
                  <button
                    onClick={() => addDiscoveredPrinter(printer)}
                    className="success"
                    style={{ width: '100%' }}
                  >
                    Add Printer
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Configured Printers ({printers.length})</h3>
          <button
            onClick={() => setShowManualAdd(!showManualAdd)}
            className="secondary"
          >
            {showManualAdd ? 'Cancel' : 'Add Manually'}
          </button>
        </div>

        {showManualAdd && (
          <div className="card" style={{ marginTop: '1rem' }}>
            <h4>Add Printer Manually</h4>
            <div className="form-group">
              <label>Printer ID (unique)</label>
              <input
                type="text"
                value={manualPrinter.id}
                onChange={(e) => setManualPrinter({ ...manualPrinter, id: e.target.value })}
                placeholder="warehouse_zebra_1"
              />
            </div>
            <div className="form-group">
              <label>Display Name</label>
              <input
                type="text"
                value={manualPrinter.display_name}
                onChange={(e) => setManualPrinter({ ...manualPrinter, display_name: e.target.value })}
                placeholder="Warehouse Zebra Printer"
              />
            </div>
            <div className="form-group">
              <label>IP Address</label>
              <input
                type="text"
                value={manualPrinter.ip}
                onChange={(e) => setManualPrinter({ ...manualPrinter, ip: e.target.value })}
                placeholder="192.168.1.100"
              />
            </div>
            <div className="form-group">
              <label>Port</label>
              <input
                type="number"
                value={manualPrinter.port}
                onChange={(e) => setManualPrinter({ ...manualPrinter, port: parseInt(e.target.value) })}
              />
            </div>
            <div className="form-group">
              <label>Location (optional)</label>
              <input
                type="text"
                value={manualPrinter.location}
                onChange={(e) => setManualPrinter({ ...manualPrinter, location: e.target.value })}
                placeholder="Warehouse Bay 3"
              />
            </div>
            <button onClick={addManualPrinter} className="primary">
              Add Printer
            </button>
          </div>
        )}

        {printers.length > 0 ? (
          <div className="printer-grid" style={{ marginTop: '1rem' }}>
            {printers.map((printer) => (
              <div
                key={printer.id}
                className={`printer-card ${printer.status || 'unknown'}`}
              >
                <div className="printer-header">
                  <div>
                    <strong>{printer.config?.display_name || printer.id}</strong>
                    <div style={{ fontSize: '0.875rem', opacity: 0.8 }}>
                      {printer.config?.ip && `${printer.config.ip}:${printer.config.port || 9100}`}
                    </div>
                    {printer.config?.location && (
                      <div style={{ fontSize: '0.875rem', opacity: 0.6 }}>
                        📍 {printer.config.location}
                      </div>
                    )}
                  </div>
                  <span className={`badge ${printer.status === 'online' ? 'success' : 'danger'}`}>
                    {printer.status || 'unknown'}
                  </span>
                </div>
                <div className="printer-actions">
                  <button
                    onClick={() => removePrinter(printer.id)}
                    className="danger"
                    style={{ width: '100%' }}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ marginTop: '1rem', opacity: 0.8 }}>
            No printers configured yet. Scan the network or add manually.
          </p>
        )}
      </div>
    </div>
  );
}

export default PrinterDiscovery;
