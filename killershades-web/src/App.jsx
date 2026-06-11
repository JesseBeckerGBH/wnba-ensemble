import React from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import BerlinettaCockpit from './pages/BerlinettaCockpit';
import LaFerrariCockpit from './pages/LaFerrariCockpit';
import CarbonPanel from './components/CarbonPanel';
import './App.css';

/**
 * The Garage Landing Page Component
 */
const Garage = () => {
  const navigate = useNavigate();

  return (
    <div style={{ padding: '40px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ 
        fontFamily: 'var(--font-dash)', 
        color: '#fff', 
        textAlign: 'center',
        textTransform: 'uppercase',
        letterSpacing: '10px',
        fontSize: '4rem',
        textShadow: '0 0 30px rgba(255,255,255,0.2)',
        marginBottom: '60px'
      }}>
        The Garage
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '40px' }}>
        
        {/* BERLINETTA TIER SELECTION */}
        <CarbonPanel title="Berlinetta Tier" style={{ cursor: 'pointer' }}>
          <div onClick={() => navigate('/berlinetta')}>
            <p style={{ color: '#ccc', fontSize: '1.2rem', lineHeight: '1.6' }}>
              Deep Statistical Arbitrage.<br/>
              WNBA & Pro Golf Models.<br/>
              Optimized for steady, long-term yield.
            </p>
            <div style={{ marginTop: '30px', borderTop: '1px solid #333', paddingTop: '20px' }}>
              <span className="digital-readout" style={{ color: '#aaa', borderColor: '#555', boxShadow: 'none' }}>
                ENTER COCKPIT // $99/mo
              </span>
            </div>
          </div>
        </CarbonPanel>

        {/* LA FERRARI TIER SELECTION */}
        <CarbonPanel title="LaFerrari Tier" style={{ cursor: 'pointer', border: '2px solid var(--rosso-corsa)', boxShadow: '0 0 20px rgba(212,0,0,0.4)' }}>
          <div onClick={() => navigate('/laferrari')}>
            <p style={{ color: '#ccc', fontSize: '1.2rem', lineHeight: '1.6' }}>
              Relativistic High-Frequency Arbitrage.<br/>
              Darts CV Engine.<br/>
              Sub-millisecond momentum extraction.
            </p>
            <div style={{ marginTop: '30px', borderTop: '1px solid var(--rosso-corsa)', paddingTop: '20px' }}>
              <span className="digital-readout punk-glow">
                ENTER COCKPIT // $999/mo
              </span>
            </div>
          </div>
        </CarbonPanel>

      </div>
    </div>
  );
};

function App() {
  return (
    <Routes>
      <Route path="/" element={<Garage />} />
      <Route path="/berlinetta" element={<BerlinettaCockpit />} />
      <Route path="/laferrari" element={<LaFerrariCockpit />} />
    </Routes>
  );
}

export default App;
