import React, { useState, useEffect, useRef } from 'react';
import { Cpu, Activity } from 'lucide-react';

const BeastDashboard = ({ activeTier }) => {
  const [alphaThreshold, setAlphaThreshold] = useState(4.5);
  const [kellyMultiplier, setKellyMultiplier] = useState(1.0);
  const [stochasticActive, setStochasticActive] = useState(true);
  
  const [logs, setLogs] = useState([
    "> INITIALIZING POLYGLOT STACK...",
    "> BINDING TO: 192.168.1.100:5432 (SYNDICATE_DB)",
    "> C++ EXECUTION INTERFACE: [ SHADOW_MODE_ENGAGED - $10000.00 SIMULATED ]",
    "> RUST MATHEMATICS ENGINE: OK",
    "> AWAITING LIVE FIX API WEBSOCKET FEED..."
  ]);
  const [liveStats, setLiveStats] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    // Connect to the mock websocket server
    const ws = new WebSocket('ws://localhost:8080');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'INIT') {
        setLogs(prev => [...prev, `> [CONNECTED] ${data.event} | ${data.combatants.a} vs ${data.combatants.b}`]);
        setLiveStats(data);
      } else if (data.type === 'TICK') {
        setLiveStats(data);
        if (data.is_major) {
           setLogs(prev => [...prev, `> [${new Date().toLocaleTimeString('en-US',{hour12:false})}.${new Date().getMilliseconds().toString().padStart(3,'0')}] !!! ${data.live_event} !!! PROB SHIFT: P(A)=${data.win_prob_a} Edge=${data.edge}`]);
        } else {
           // Optionally add minor log ticks, but usually we just update the live stats gauge
           // setLogs(prev => [...prev, `> TIC: ${data.win_prob_a}`])
        }
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div style={{ padding: '2rem', display: 'flex', gap: '2rem', height: '100%', alignItems: 'flex-start' }}>
      {/* Control Panel */}
      <div className="panel" style={{ width: '380px', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        <h2 style={{ fontSize: '1.75rem', margin: '0', display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--accent-positive)', fontFamily: 'monospace' }}>
          <Cpu size={28}/> BEAST v2
        </h2>
        
        <div>
          <label className="mono-text" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            <span>ALPHA THRESHOLD CONSTRAINT</span>
            <span style={{ color: 'var(--accent-positive)' }}>&ge; {alphaThreshold}% EV</span>
          </label>
          <input type="range" min="1" max="10" step="0.1" value={alphaThreshold} onChange={(e) => setAlphaThreshold(e.target.value)} style={{ width: '100%', accentColor: 'var(--accent-positive)' }} />
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Blocks execution if the true edge fails to breach threshold relative to Pinnacle closing lines.</p>
        </div>

        <div>
           <label className="mono-text" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
            <span>KELLY CRITERION AGGRESSION</span>
            <span style={{ color: 'var(--accent-positive)' }}>{kellyMultiplier}x</span>
          </label>
          <input type="range" min="0.1" max="2.0" step="0.1" value={kellyMultiplier} onChange={(e) => setKellyMultiplier(e.target.value)} style={{ width: '100%', accentColor: 'var(--accent-positive)' }} />
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Adjusts bet sizing logic. 1x establishes Full Kelly mathematical geometric growth.</p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '4px', border: '1px solid var(--border-light)' }}>
          <div>
            <span className="mono-text" style={{ color: 'var(--text-primary)', display: 'block' }}>STOCHASTIC CONSENSUS</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Gemini LLM Anomalistic Routing</span>
          </div>
          <button 
            onClick={() => setStochasticActive(!stochasticActive)}
            style={{ 
              background: stochasticActive ? 'var(--accent-positive)' : 'transparent', 
              color: stochasticActive ? '#000' : 'var(--text-secondary)', 
              border: stochasticActive ? 'none' : '1px solid var(--text-secondary)', 
              padding: '0.5rem 1rem', cursor: 'pointer', borderRadius: '4px', fontWeight: 'bold' 
            }}
          >
            {stochasticActive ? 'ON' : 'OFF'}
          </button>
        </div>

        <button style={{ width: '100%', padding: '1rem', background: 'var(--text-primary)', color: '#000', border: 'none', borderRadius: '4px', fontWeight: 900, cursor: 'pointer', letterSpacing: '1px', marginTop: '1rem' }}>
          UPDATE XGBOOST WEIGHTS
        </button>
      </div>

      {/* Terminal View */}
      <div className="panel" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <h3 className="mono-text" style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={20} color="var(--accent-positive)"/> LIVE EXECUTION STREAM
        </h3>
        <p style={{ color: 'var(--text-secondary)' }}>Monitoring TimescaleDB ingestion matrices. Booting dry-run protocols...</p>
        
        <div ref={scrollRef} style={{ flexGrow: 1, minHeight: '300px', maxHeight: '400px', background: 'rgba(9, 9, 11, 0.95)', border: '1px solid var(--border-light)', borderRadius: '4px', padding: '1.5rem', fontFamily: 'monospace', overflowY: 'auto' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', color: 'var(--text-secondary)' }}>
                {logs.map((log, index) => (
                    <span key={index} style={{ color: log.includes('!!!') ? '#fbbf24' : log.includes('CONNECTED') ? 'var(--accent-positive)' : 'var(--text-secondary)' }}>
                        {log}
                    </span>
                ))}
                {logs.length === 5 && <span style={{ color: 'var(--accent-positive)' }} className="animate-pulse">_</span>}
            </div>
        </div>

        {liveStats && (
            <div style={{ marginTop: '1.5rem', background: 'rgba(0,0,0,0.5)', padding: '1.5rem', borderRadius: '4px', border: '1px solid var(--accent-positive)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    <strong style={{ color: 'var(--text-primary)', fontSize: '1.2rem' }}>LIVE TELEMETRY: {liveStats.event || 'UFC Live'}</strong>
                    <span className="animate-pulse" style={{ color: 'var(--accent-positive)' }}>● LIVE STREAM</span>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', textAlign: 'center' }}>
                    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '4px' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>MODEL PROB (VOLK)</div>
                        <div style={{ fontSize: '2rem', fontFamily: 'monospace', color: liveStats.win_prob_a > 0.6 ? 'var(--accent-positive)' : 'var(--text-primary)' }}>
                            {(liveStats.win_prob_a * 100).toFixed(1)}%
                        </div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '4px' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>MODEL PROB (LOPES)</div>
                        <div style={{ fontSize: '2rem', fontFamily: 'monospace', color: liveStats.win_prob_b > 0.5 ? 'var(--accent-positive)' : 'var(--text-primary)' }}>
                            {(liveStats.win_prob_b * 100).toFixed(1)}%
                        </div>
                    </div>
                     <div style={{ background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '4px', border: liveStats.edge > 0.05 ? '1px solid var(--accent-positive)' : 'none' }}>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>REAL-TIME EDGE (CLV)</div>
                        <div style={{ fontSize: '2rem', fontFamily: 'monospace', color: liveStats.edge > 0 ? '#10b981' : '#ef4444' }}>
                            {(liveStats.edge * 100).toFixed(1)}%
                        </div>
                        {liveStats.edge > 0.05 && <div style={{ fontSize: '0.6rem', color: '#10b981', marginTop: '0.2rem', textTransform: 'uppercase' }}>Auto-Execution Armed</div>}
                    </div>
                </div>
            </div>
        )}
      </div>
    </div>
  );
};

export default BeastDashboard;
