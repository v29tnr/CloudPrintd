import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { setupAPI, printersAPI } from '../api';
import ConnectivitySelector from './ConnectivitySelector';
import PrinterDiscovery from './PrinterDiscovery';
import APITokenGenerator from './APITokenGenerator';

const STEPS = [
  { number: 1, label: 'Welcome' },
  { number: 2, label: 'Connectivity' },
  { number: 3, label: 'Printers' },
  { number: 4, label: 'API Security' },
  { number: 5, label: 'Complete' },
];

function SetupWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [setupData, setSetupData] = useState({
    connectivity: { method: 'none' },
    printers: [],
    apiToken: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if setup is already completed
    setupAPI.getStatus().then(response => {
      if (response.data.setup_completed) {
        navigate('/');
      }
    }).catch(err => {
      console.error('Failed to check setup status:', err);
    });
  }, [navigate]);

  const nextStep = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
      setError(null);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      setError(null);
    }
  };

  const updateSetupData = (field, value) => {
    setSetupData(prev => ({ ...prev, [field]: value }));
  };

  const completeSetup = async () => {
    setLoading(true);
    setError(null);

    try {
      // Mark setup as complete
      await setupAPI.complete();
      
      // Redirect to dashboard
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to complete setup');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div>
            <h2>Welcome to CloudPrintd</h2>
            <p>
              CloudPrintd is your self-hosted print server that bridges Salesforce cloud 
              to your on-site printers, especially Zebra ZPL thermal printers.
            </p>
            <p style={{ marginTop: '1rem' }}>
              This wizard will guide you through:
            </p>
            <ul style={{ marginLeft: '2rem', marginTop: '1rem' }}>
              <li>Setting up network connectivity</li>
              <li>Discovering and configuring printers</li>
              <li>Securing your API access</li>
              <li>Testing your configuration</li>
            </ul>
            <p style={{ marginTop: '1rem', fontStyle: 'italic' }}>
              Estimated time: 5-10 minutes
            </p>
          </div>
        );

      case 2:
        return (
          <ConnectivitySelector
            selected={setupData.connectivity}
            onChange={(connectivity) => updateSetupData('connectivity', connectivity)}
          />
        );

      case 3:
        return (
          <PrinterDiscovery
            printers={setupData.printers}
            onChange={(printers) => updateSetupData('printers', printers)}
          />
        );

      case 4:
        return (
          <APITokenGenerator
            token={setupData.apiToken}
            onTokenGenerated={(token) => updateSetupData('apiToken', token)}
          />
        );

      case 5:
        return (
          <div>
            <h2>Setup Complete!</h2>
            <div className="success-message" style={{ marginTop: '2rem' }}>
              <h3>🎉 Configuration Summary</h3>
            </div>
            
            <div className="card" style={{ marginTop: '1rem' }}>
              <h4>Connectivity</h4>
              <p>Method: <strong>{setupData.connectivity.method || 'None'}</strong></p>
            </div>

            <div className="card" style={{ marginTop: '1rem' }}>
              <h4>Printers Configured</h4>
              <p><strong>{setupData.printers.length}</strong> printer(s)</p>
              {setupData.printers.length > 0 && (
                <ul>
                  {setupData.printers.slice(0, 5).map((printer, idx) => (
                    <li key={idx}>{printer.display_name || printer.id}</li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card" style={{ marginTop: '1rem' }}>
              <h4>API Security</h4>
              <p>API token: <strong>{setupData.apiToken ? 'Generated ✓' : 'Not generated'}</strong></p>
            </div>

            <div className="instructions" style={{ marginTop: '2rem' }}>
              <h4>Next Steps:</h4>
              <ol style={{ marginLeft: '1.5rem', marginTop: '0.5rem' }}>
                <li>Click "Finish" to complete setup</li>
                <li>Configure your Salesforce Named Credential with the API token</li>
                <li>Send a test print job from Salesforce</li>
              </ol>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="wizard-container">
      <div className="wizard-header">
        <h1>CloudPrintd Setup Wizard</h1>
      </div>

      <div className="wizard-progress">
        {STEPS.map((step) => (
          <div
            key={step.number}
            className={`wizard-step ${
              currentStep === step.number ? 'active' : ''
            } ${currentStep > step.number ? 'completed' : ''}`}
          >
            <div className="step-circle">
              {currentStep > step.number ? '✓' : step.number}
            </div>
            <div className="step-label">{step.label}</div>
          </div>
        ))}
      </div>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="wizard-content card">
        {renderStepContent()}
      </div>

      <div className="wizard-navigation">
        <button
          onClick={prevStep}
          disabled={currentStep === 1 || loading}
          className="secondary"
        >
          Previous
        </button>
        
        {currentStep < STEPS.length ? (
          <button
            onClick={nextStep}
            disabled={loading}
            className="primary"
          >
            Next
          </button>
        ) : (
          <button
            onClick={completeSetup}
            disabled={loading}
            className="success"
          >
            {loading ? 'Completing...' : 'Finish Setup'}
          </button>
        )}
      </div>
    </div>
  );
}

export default SetupWizard;
