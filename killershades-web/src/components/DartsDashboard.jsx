import React, { useState } from 'react';
import { Crosshair, Activity } from 'lucide-react';

const DartsDashboard = ({ activeTier }) => {
  const [openingWeight, setOpeningWeight] = useState(70);
  const [formMetric, setFormMetric] = useState(1.5);
  const [microstructureActive, setMicrostructureActive] = useState(true);

  return (
    <div style={{ padding: '2rem', display: 'flex', gap: '2rem', height: '100%', alignItems: 'flex-start' }}>
      {/* Control Panel */}
      <div className="panel" style={{ width: '380px', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        <h2 style={{ fontSize: '1.75rem', margin: '0', display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--accent-positive)', fontFamily: 'monospace' }}>
          <Crosshair size={28}/> DARTS v2
        </h2>
        
        <div>
          <label className="mono-text" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            <span>MARKET PRIOR WEIGHT</span>
            <span style={{ color: 'var(--accent-positive)' }}>{openingWeight}%</span>
          </label>
          <input type="range" min="10" max="90" step="5" value={openingWeight} onChange={(e) => setOpeningWeight(e.target.value)} style={{ width: '100%', accentColor: 'var(--accent-positive)' }} />
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Adjusts reliance on Opening Line Value vs native ELO calculations.</p>
        </div>

        <div>
           <label className="mono-text" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            <span>FORM / FATIGUE RATIO</span>
            <span style={{ color: 'var(--accent-positive)' }}>{formMetric}x</span>
          </label>
          <input type="range" min="0.5" max="3.0" step="0.1" value={formMetric} onChange={(e) => setFormMetric(e.target.value)} style={{ width: '100%', accentColor: 'var(--accent-positive)' }} />
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Weights recent tournament throwing velocity and psychological degradation metrics.</p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '4px', border: '1px solid var(--border-light)' }}>
          <div>
            <span className="mono-text" style={{ color: 'var(--text-primary)', display: 'block' }}>LIVE MICROSTRUCTURE</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>In-Play Options Skew Analysis</span>
          </div>
          <button 
            onClick={() => setMicrostructureActive(!microstructureActive)}
            style={{ 
              background: microstructureActive ? 'var(--accent-positive)' : 'transparent', 
              color: microstructureActive ? '#000' : 'var(--text-secondary)', 
              border: microstructureActive ? 'none' : '1px solid var(--text-secondary)', 
              padding: '0.5rem 1rem', cursor: 'pointer', borderRadius: '4px', fontWeight: 'bold' 
            }}
          >
            {microstructureActive ? 'ARMED' : 'DISARMED'}
          </button>
        </div>

        <button style={{ width: '100%', padding: '1rem', background: 'var(--text-primary)', color: '#000', border: 'none', borderRadius: '4px', fontWeight: 900, cursor: 'pointer', letterSpacing: '1px', marginTop: '1rem' }}>
          UPDATE DARTS ENGINE
        </button>
      </div>

      {/* Terminal View */}
      <div className="panel" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <h3 className="mono-text" style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={20} color="var(--accent-positive)"/> IN-PLAY ORDER BOOK
        </h3>
        <p style={{ color: 'var(--text-secondary)' }}>Awaiting Live PDC / WDF WebSockets...</p>
        
        <div style={{ flexGrow: 1, minHeight: '400px', background: 'rgba(9, 9, 11, 0.95)', border: '1px solid var(--border-light)', borderRadius: '4px', padding: '1.5rem', fontFamily: 'monospace', overflowY: 'auto' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', color: 'var(--text-secondary)' }}>
                <span>&gt; Pinging European feeds...</span>
                <span>&gt; Latency check: 18ms</span>
                <span style={{ color: 'var(--text-primary)' }}>&gt; SHADOW MODE ENGAGED. READY FOR TARGET ACQUISITION.</span>
            </div>
        </div>
      </div>
    </div>
  );
};

export default DartsDashboard;
