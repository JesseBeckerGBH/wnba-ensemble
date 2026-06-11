import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Cpu, Activity, ShieldAlert, Sliders, Play, Disc } from 'lucide-react';
import CarbonPanel from '../components/CarbonPanel';
import CockpitDial from '../components/CockpitDial';

const LaFerrariCockpit = () => {
  const navigate = useNavigate();
  const [alphaThreshold, setAlphaThreshold] = useState(4.5);
  const [kellyMultiplier, setKellyMultiplier] = useState(1.0);
  const [stochasticActive, setStochasticActive] = useState(true);
  const [executionArmed, setExecutionArmed] = useState(false);
  
  const [logs, setLogs] = useState([
    "> INITIALIZING HIGH-FREQUENCY TELEMETRY...",
    "> BINDING METRICS TO DARTS OCR CORE...",
    "> C++ SPEED LAYER: ACTIVE (LATENCY CAP: 300ms)",
    "> RUST KINEMATICS ENGINE: OK",
    "> AWAITING LIVE FIX API WEBSOCKET FEED..."
  ]);
  const [liveStats, setLiveStats] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    // Connect to the websocket server via environment variable
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8080';
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setLogs(prev => [...prev, "> [WS] WEBSOCKET CONNECTION ESTABLISHED ON ws://localhost:8080"]);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'INIT') {
        setLogs(prev => [...prev, `> [CONNECTED] ${data.event} | ${data.combatants.a} vs ${data.combatants.b}`]);
        setLiveStats(data);
      } else if (data.type === 'TICK') {
        setLiveStats(data);
        if (data.is_major) {
           setLogs(prev => [...prev, `> [${new Date().toLocaleTimeString('en-US',{hour12:false})}.${new Date().getMilliseconds().toString().padStart(3,'0')}] !!! ${data.live_event} !!! PROB SHIFT: P(A)=${data.win_prob_a} Edge=${data.edge}`]);
        }
      }
    };

    ws.onerror = (err) => {
      setLogs(prev => [...prev, `> [WS ERROR] Failed to connect to ws://localhost:8080. Fallback telemetry active.`]);
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

  // Fallback telemetry if WS hasn't emitted a value
  const getDisplayEdge = () => {
    if (liveStats && liveStats.edge) {
      return parseFloat(liveStats.edge) * 100;
    }
    return 12.5; // fallback edge
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#0a0a0a', color: '#fff' }}>
      
      {/* COCKPIT NAVIGATION BAR */}
      <div style={{ padding: '15px 30px', borderBottom: '2px solid var(--rosso-corsa)', background: '#111', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 4px 15px rgba(212,0,0,0.2)' }}>
        <button className="neon-btn" onClick={() => navigate('/')} style={{ padding: '8px 20px', fontSize: '0.9rem' }}>
          &lt; EXIT COCKPIT
        </button>
        <span style={{ fontFamily: 'var(--font-dash)', color: '#fff', fontSize: '1.6rem', letterSpacing: '4px' }}>
          LA FERRARI // REAL-TIME SPEED ARBITRAGE
        </span>
      </div>

      {/* DASHBOARD VIEWPORT */}
      <div style={{ flex: 1, padding: '30px', display: 'flex', flexDirection: 'column', gap: '30px', maxWidth: '1400px', margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        
        {/* ROW 1: DIALS & CONTROL PANEL */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '30px' }}>
          
          <CarbonPanel title="Relativistic Speed Dial" style={{ border: '1px solid var(--rosso-corsa)' }}>
            <div style={{ display: 'flex', justifyContent: 'center', padding: '10px 0' }}>
              <CockpitDial value={getDisplayEdge()} label="MOMENTUM VELOCITY %" maxValue={50} />
            </div>
          </CarbonPanel>

          <CarbonPanel title="Steering Wheel Parameters">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '10px 0' }}>
              <div>
                <label className="mono-text" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
                  <span>ALPHA THRESHOLD EV</span>
                  <span style={{ color: 'var(--rosso-corsa)', fontWeight: 'bold' }}>&ge; {alphaThreshold}%</span>
                </label>
                <input 
                  type="range" min="1" max="10" step="0.1" 
                  value={alphaThreshold} onChange={(e) => setAlphaThreshold(parseFloat(e.target.value))} 
                  style={{ width: '100%', accentColor: 'var(--rosso-corsa)', cursor: 'pointer' }} 
                />
              </div>

              <div>
                <label className="mono-text" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
                  <span>KELLY MULTIPLIER</span>
                  <span style={{ color: 'var(--rosso-corsa)', fontWeight: 'bold' }}>{kellyMultiplier}x</span>
                </label>
                <input 
                  type="range" min="0.1" max="2.0" step="0.1" 
                  value={kellyMultiplier} onChange={(e) => setKellyMultiplier(parseFloat(e.target.value))} 
                  style={{ width: '100%', accentColor: 'var(--rosso-corsa)', cursor: 'pointer' }} 
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 15px', background: 'rgba(255,255,255,0.03)', borderRadius: '4px', border: '1px solid #333' }}>
                <div>
                  <span className="mono-text" style={{ display: 'block', fontSize: '0.8rem' }}>STOCHASTIC CONSENSUS</span>
                  <span style={{ fontSize: '0.65rem', color: '#666' }}>Parallel LLM verification</span>
                </div>
                <button 
                  onClick={() => setStochasticActive(!stochasticActive)}
                  style={{ 
                    background: stochasticActive ? 'var(--rosso-corsa)' : 'transparent', 
                    color: '#fff', 
                    border: stochasticActive ? 'none' : '1px solid #555', 
                    padding: '5px 12px', cursor: 'pointer', borderRadius: '4px', fontWeight: 'bold', fontSize: '0.8rem'
                  }}
                >
                  {stochasticActive ? 'ON' : 'OFF'}
                </button>
              </div>
            </div>
          </CarbonPanel>

          <CarbonPanel title="Execution Overlay">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '10px 0', justifyContent: 'space-between', height: '100%', boxSizing: 'border-box' }}>
              <div style={{ background: '#070707', padding: '15px', borderRadius: '4px', border: '1px solid #222', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: '#555', textTransform: 'uppercase' }}>C++ Execution Mode</div>
                <div className={`digital-readout punk-glow`} style={{ fontSize: '1.4rem', color: executionArmed ? 'var(--rosso-corsa)' : '#bbb', marginTop: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                  <Disc className={executionArmed ? "animate-spin" : ""} size={18} color={executionArmed ? "var(--rosso-corsa)" : "#888"}/>
                  {executionArmed ? 'ARMED // LIVE' : 'SHADOW // TEST'}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '15px' }}>
                <button 
                  className={`neon-btn ${executionArmed ? '' : 'yellow'}`} 
                  style={{ flex: 1, padding: '12px', fontSize: '0.9rem' }}
                  onClick={() => setExecutionArmed(!executionArmed)}
                >
                  {executionArmed ? 'DISARM ENGINE' : 'ARM FOR LIVE EXEC'}
                </button>
              </div>
            </div>
          </CarbonPanel>

        </div>

        {/* ROW 2: LIVE TELEMETRY TERMINAL & CHARTS */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '30px' }}>
          
          <CarbonPanel title="Live Speed Ingestion stream">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: '#666', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <Activity size={14} className="animate-pulse" color="var(--rosso-corsa)"/> Ingestion topic: odds_ticker
                </span>
                <span style={{ fontSize: '0.8rem', color: '#666' }}>PORT 8080</span>
              </div>
              <div ref={scrollRef} style={{ height: '300px', background: 'rgba(5, 5, 5, 0.95)', border: '1px solid #222', borderRadius: '4px', padding: '15px', fontFamily: 'monospace', overflowY: 'auto', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {logs.map((log, index) => (
                    <div key={index} style={{ 
                      color: log.includes('!!!') ? 'var(--rosso-corsa)' : log.includes('CONNECTED') ? '#10b981' : '#888',
                      lineHeight: '1.4'
                    }}>
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CarbonPanel>

          <CarbonPanel title="Current In-Play Tick Details">
            {liveStats ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '5px 0' }}>
                <div style={{ borderBottom: '1px solid #222', paddingBottom: '10px' }}>
                  <div style={{ fontSize: '0.75rem', color: '#555' }}>ACTIVE EVENT</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 'bold', marginTop: '5px' }}>{liveStats.event || 'UFC Live / Darts Live'}</div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                  <div style={{ background: '#111', padding: '12px', borderRadius: '4px', border: '1px solid #222' }}>
                    <div style={{ fontSize: '0.7rem', color: '#555' }}>P(a): {liveStats.combatants?.a || 'A'}</div>
                    <div style={{ fontSize: '1.5rem', fontFamily: 'monospace', color: 'var(--rosso-corsa)', marginTop: '5px' }}>
                      {(parseFloat(liveStats.win_prob_a) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div style={{ background: '#111', padding: '12px', borderRadius: '4px', border: '1px solid #222' }}>
                    <div style={{ fontSize: '0.7rem', color: '#555' }}>P(b): {liveStats.combatants?.b || 'B'}</div>
                    <div style={{ fontSize: '1.5rem', fontFamily: 'monospace', color: '#aaa', marginTop: '5px' }}>
                      {(parseFloat(liveStats.win_prob_b) * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div style={{ background: '#111', padding: '15px', borderRadius: '4px', border: '1px solid #222' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#555' }}>ESTIMATED ALPHA EDGE</div>
                      <div style={{ fontSize: '1.8rem', fontFamily: 'monospace', color: '#10b981', fontWeight: 'bold', marginTop: '5px' }}>
                        +{(parseFloat(liveStats.edge) * 100).toFixed(1)}%
                      </div>
                    </div>
                    {parseFloat(liveStats.edge) > 0.05 && (
                      <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', padding: '4px 10px', borderRadius: '3px', fontSize: '0.7rem', fontWeight: 'bold' }}>
                        EDGE EXCEEDS ALPHA
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ padding: '40px', textAlign: 'center', color: '#666', fontFamily: 'monospace' }}>
                Awaiting connection to mock WebSocket stream...
              </div>
            )}
          </CarbonPanel>

        </div>

      </div>
    </div>
  );
};

export default LaFerrariCockpit;
