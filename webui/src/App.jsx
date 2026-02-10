import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SetupWizard from './components/SetupWizard';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/setup" element={<SetupWizard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
