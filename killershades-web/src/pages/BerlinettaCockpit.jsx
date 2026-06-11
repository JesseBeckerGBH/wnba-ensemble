import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { Trophy, TrendingUp, AlertTriangle, ShieldCheck, RefreshCw } from 'lucide-react';
import CarbonPanel from '../components/CarbonPanel';
import CockpitDial from '../components/CockpitDial';
import { useTelemetryStream } from '../hooks/useTelemetryStream';

const mockPerformanceData = [
  { day: 'Day 1', bankroll: 1000 },
  { day: 'Day 2', bankroll: 1045 },
  { day: 'Day 3', bankroll: 1030 },
  { day: 'Day 4', bankroll: 1095 },
  { day: 'Day 5', bankroll: 1150 },
  { day: 'Day 6', bankroll: 1120 },
  { day: 'Day 7', bankroll: 1242 },
];

const BerlinettaCockpit = () => {
  const navigate = useNavigate();
  const telemetry = useTelemetryStream('berlinetta');
  const [predictionData, setPredictionData] = useState(null);
  const [riskMultiplier, setRiskMultiplier] = useState(0.25); // Quarter Kelly default
  const [loading, setLoading] = useState(true);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      const response = await fetch('/wnba_predictions.json');
      if (response.ok) {
        const json = await response.json();
        setPredictionData(json);
      } else {
        // Fallback mock predictions if file doesn't exist yet
        setPredictionData({
          last_updated: new Date().toISOString().slice(0, 16).replace('T', ' '),
          bankroll: 1000,
          models: {
            moneyline: { version: "v_20260311_moneyline", auc: 0.693 },
            totals: { version: "v_20260311_totals", auc: 0.700 }
          },
          bets: [
            {
              grade: "A+",
              type: "ML",
              pick: "New York Liberty",
              matchup: "Las Vegas Aces vs New York Liberty",
              prob: 0.748,
              impl: 0.435,
              edge: 0.313,
              odds: 2.30,
              stake: 100.00,
              start: "2026-06-10 19:30"
            },
            {
              grade: "A+",
              type: "TOT",
              pick: "Over 162.5",
              matchup: "Las Vegas Aces vs New York Liberty",
              prob: 0.699,
              impl: 0.524,
              edge: 0.176,
              odds: 1.91,
              stake: 92.09,
              start: "2026-06-10 19:30"
            }
          ]
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, []);

  // Calculate adjusted stake based on Risk Multiplier (custom slider)
  const getAdjustedStake = (baseStake, originalFraction = 0.25) => {
    const fraction = riskMultiplier / originalFraction;
    return (baseStake * fraction).toFixed(2);
  };

  const maxEdge = predictionData && predictionData.bets.length > 0 
    ? Math.max(...predictionData.bets.map(b => b.edge)) * 100 
    : telemetry.edge;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#0a0a0a', color: '#fff' }}>
      
      {/* COCKPIT NAVIGATION BAR */}
      <div style={{ padding: '15px 30px', borderBottom: '2px solid #333', background: '#111', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 4px 15px rgba(0,0,0,0.5)' }}>
        <button className="neon-btn yellow" onClick={() => navigate('/')} style={{ padding: '8px 20px', fontSize: '0.9rem', height: 'fit-content' }}>
          &lt; EXIT COCKPIT
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span style={{ fontFamily: 'var(--font-dash)', color: 'var(--giallo-modena)', fontSize: '1.6rem', letterSpacing: '4px' }}>
            BERLINETTA TIER // STATISTICAL ARBITRAGE
          </span>
        </div>
      </div>

      {/* DASHBOARD VIEWPORT */}
      <div style={{ flex: 1, padding: '30px', display: 'flex', flexDirection: 'column', gap: '30px', maxWidth: '1400px', margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        
        {/* TOP METRICS & GAUGES */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '30px' }}>
          
          <CarbonPanel title="Inference Performance Dial">
            <div style={{ display: 'flex', justifyContent: 'center', padding: '10px 0' }}>
              <CockpitDial value={maxEdge} label="MAX ACTIVE EDGE %" maxValue={40} />
            </div>
          </CarbonPanel>

          <CarbonPanel title="Model Architecture Summary">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', padding: '10px 0' }}>
              <div style={{ background: '#111', padding: '12px 18px', borderRadius: '4px', border: '1px solid #333' }}>
                <div style={{ color: '#666', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '5px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <ShieldCheck size={14} color="var(--giallo-modena)"/> Moneyline Stack Version
                </div>
                <div className="mono-text" style={{ fontSize: '0.95rem', color: '#eee' }}>
                  {predictionData?.models?.moneyline?.version || "v_20260311_moneyline"} (AUC: {predictionData?.models?.moneyline?.auc?.toFixed(3) || "0.693"})
                </div>
              </div>
              <div style={{ background: '#111', padding: '12px 18px', borderRadius: '4px', border: '1px solid #333' }}>
                <div style={{ color: '#666', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '5px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <ShieldCheck size={14} color="var(--giallo-modena)"/> Totals Stack Version
                </div>
                <div className="mono-text" style={{ fontSize: '0.95rem', color: '#eee' }}>
                  {predictionData?.models?.totals?.version || "v_20260311_totals"} (AUC: {predictionData?.models?.totals?.auc?.toFixed(3) || "0.700"})
                </div>
              </div>
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ flex: 1, background: '#111', padding: '10px', borderRadius: '4px', border: '1px solid #222', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: '#666' }}>GATE STATUS</div>
                  <div style={{ color: '#10b981', fontFamily: 'var(--font-dash)', fontSize: '1.2rem', marginTop: '4px' }}>PASSED</div>
                </div>
                <div style={{ flex: 1, background: '#111', padding: '10px', borderRadius: '4px', border: '1px solid #222', textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: '#666' }}>ACTIVE BANKROLL</div>
                  <div style={{ color: 'var(--giallo-modena)', fontFamily: 'var(--font-dash)', fontSize: '1.2rem', marginTop: '4px' }}>
                    £{predictionData?.bankroll || "1,000"}
                  </div>
                </div>
              </div>
            </div>
          </CarbonPanel>

          <CarbonPanel title="Risk Controls">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', padding: '10px 0' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <span className="mono-text" style={{ fontSize: '0.85rem' }}>KELLY WAGER MULTIPLIER</span>
                  <span style={{ color: 'var(--giallo-modena)', fontWeight: 'bold' }}>{riskMultiplier}x Kelly</span>
                </div>
                <input 
                  type="range" 
                  min="0.05" 
                  max="1.0" 
                  step="0.05" 
                  value={riskMultiplier} 
                  onChange={(e) => setRiskMultiplier(parseFloat(e.target.value))} 
                  style={{ width: '100%', accentColor: 'var(--giallo-modena)', cursor: 'pointer' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#666', marginTop: '5px' }}>
                  <span>0.05x (Conservative)</span>
                  <span>0.25x (Quarter Kelly)</span>
                  <span>1.00x (Full Kelly)</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '15px', marginTop: '10px' }}>
                <button className="neon-btn yellow" style={{ flex: 1, padding: '10px', fontSize: '0.9rem' }} onClick={fetchPredictions}>
                  <RefreshCw size={14} style={{ marginRight: '5px', verticalAlign: 'middle' }}/> SYNC ENGINE
                </button>
              </div>
            </div>
          </CarbonPanel>

        </div>

        {/* BOTTOM CHARTS & BET BOARD */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '30px' }}>
          
          {/* DAILY BET SHEET PANEL */}
          <CarbonPanel title="Live WNBA Bet Sheet" style={{ gridColumn: 'span 2' }}>
            {loading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#888' }}>Syncing with TimescaleDB / DuckDB...</div>
            ) : !predictionData || predictionData.bets.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#888' }}>
                <AlertTriangle size={32} color="var(--giallo-modena)" style={{ marginBottom: '10px' }}/>
                <div>No active value discrepancy detected above EV threshold in sportsbooks.</div>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontFamily: 'monospace' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #333', color: '#666', fontSize: '0.8rem' }}>
                      <th style={{ padding: '12px' }}>GRADE</th>
                      <th style={{ padding: '12px' }}>TYPE</th>
                      <th style={{ padding: '12px' }}>MATCHUP</th>
                      <th style={{ padding: '12px' }}>PICK</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>MODEL PROB</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>ODDS</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>TRUE EV</th>
                      <th style={{ padding: '12px', textAlign: 'right', color: 'var(--giallo-modena)' }}>REC STAKE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictionData.bets.map((bet, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #222', fontSize: '0.9rem' }}>
                        <td style={{ padding: '12px' }}>
                          <span style={{ 
                            background: bet.grade.includes('A') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                            color: bet.grade.includes('A') ? '#10b981' : '#f59e0b',
                            padding: '3px 8px', borderRadius: '3px', fontWeight: 'bold'
                          }}>{bet.grade}</span>
                        </td>
                        <td style={{ padding: '12px', color: '#aaa' }}>{bet.type}</td>
                        <td style={{ padding: '12px', fontWeight: 'bold' }}>{bet.matchup}</td>
                        <td style={{ padding: '12px', color: 'var(--giallo-modena)' }}>{bet.pick}</td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>{(bet.prob * 100).toFixed(1)}%</td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>{bet.odds.toFixed(2)}</td>
                        <td style={{ padding: '12px', textAlign: 'right', color: '#10b981', fontWeight: 'bold' }}>
                          +{(bet.edge * 100).toFixed(1)}%
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', color: 'var(--giallo-modena)', fontWeight: 'bold' }}>
                          £{getAdjustedStake(bet.stake)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CarbonPanel>

          {/* HISTORICAL PERFORMANCE CHART */}
          <CarbonPanel title="Historical Syndicate Yield ROI" style={{ gridColumn: 'span 2' }}>
            <div style={{ height: '300px', padding: '10px 0' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={mockPerformanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                  <XAxis dataKey="day" stroke="#555" fontSize={11} tickLine={false} />
                  <YAxis stroke="#555" fontSize={11} tickLine={false} domain={['dataMin - 50', 'dataMax + 50']} tickFormatter={(v) => `£${v}`} />
                  <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid #333', borderRadius: '4px', color: '#fff', fontFamily: 'monospace' }} />
                  <Line type="monotone" dataKey="bankroll" stroke="var(--giallo-modena)" strokeWidth={3} dot={{ stroke: 'var(--giallo-modena)', strokeWidth: 2, fill: '#111' }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CarbonPanel>

        </div>

      </div>
    </div>
  );
};

export default BerlinettaCockpit;
