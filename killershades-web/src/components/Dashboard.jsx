import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const mockChartData = [
  { time: '10:00', ev: 2.1 },
  { time: '10:05', ev: 2.4 },
  { time: '10:10', ev: 1.8 },
  { time: '10:15', ev: 3.5 },
  { time: '10:20', ev: 3.2 },
  { time: '10:25', ev: 4.8 },
  { time: '10:30', ev: 5.1 },
];

const mockPredictions = [
  { id: 1, match: 'Coton vs. Shinozuka', market: 'ML', type: 'Stochastic Soft Line', pick: 'Shinozuka', odds: '+110', ev: '+5.4%' },
  { id: 2, match: 'Lakers vs. Nuggets', market: 'Spread', type: 'Sharp Money Delta', pick: 'Nuggets -4.5', odds: '-110', ev: '+2.1%' },
  { id: 3, match: 'Alcaraz vs. Sinner', market: 'Totals', type: 'Synthetic Imputation', pick: 'Over 38.5', odds: '-105', ev: '+3.8%' },
];

const Dashboard = ({ activeTier }) => {
  return (
    <div style={{ padding: '2rem', height: '100vh', overflowY: 'auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', letterSpacing: '1px' }}>Live Odds Matrix</h2>
          <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)' }}>Welcome to the hub. Active Tier: <strong style={{color: 'var(--accent-positive)'}}>{activeTier}</strong></p>
        </div>
        <div style={{ padding: '0.5rem 1rem', background: 'var(--accent-positive)', color: '#000', borderRadius: '4px', fontWeight: 'bold', fontSize: '0.8rem', letterSpacing: '1px' }}>
          SYSTEM ONLINE
        </div>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="panel" style={{ height: '300px' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', letterSpacing: '1px', color: 'var(--text-secondary)' }}>AGGREGATE EV MOMENTUM (Last 30m)</h3>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={mockChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" vertical={false} />
              <XAxis dataKey="time" stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="var(--text-secondary)" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `+${value}%`} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--bg-panel)', border: '1px solid var(--border-light)', borderRadius: '4px' }} />
              <Line type="monotone" dataKey="ev" stroke="var(--accent-positive)" strokeWidth={2} dot={false} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '0.85rem', letterSpacing: '1px', color: 'var(--text-secondary)' }}>TIER RESTRICTIONS</h3>
          <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', backgroundColor: 'var(--bg-core)', borderRadius: '4px', border: '1px dashed var(--border-light)', padding: '1rem' }}>
            {activeTier === 'CORE' ? (
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Upgrade to <strong>PRO</strong> to unlock real-time WebSocket streams.</p>
            ) : (
              <div>
                <p style={{ color: 'var(--accent-positive)', fontWeight: 'bold', margin: '0 0 0.5rem 0' }}>Live Sync Active</p>
                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Latency: 14ms</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="panel">
        <h3 style={{ margin: '0 0 1.5rem 0', fontSize: '0.85rem', letterSpacing: '1px', color: 'var(--text-secondary)' }}>PROPRIETARY PREDICTIONS (MOCK DATA)</h3>
        
        <div style={{ borderBottom: '1px solid var(--border-light)', paddingBottom: '0.75rem', marginBottom: '0.5rem', display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 'bold', letterSpacing: '1px' }}>
          <div>MATCH</div>
          <div>MARKET</div>
          <div>PICK</div>
          <div>ODDS</div>
          <div>TRUE EV</div>
        </div>
        
        {mockPredictions.map((pred) => (
          <div key={pred.id} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', padding: '1.25rem 0', borderBottom: '1px solid var(--border-light)', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>{pred.match}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>{pred.type}</div>
            </div>
            <div className="mono-text" style={{ color: 'var(--text-secondary)' }}>{pred.market}</div>
            <div style={{ fontWeight: 'bold', color: 'var(--accent-brand)' }}>{pred.pick}</div>
            <div className="mono-text" style={{ color: 'var(--text-primary)' }}>{pred.odds}</div>
            <div className="mono-text" style={{ color: 'var(--accent-positive)', fontWeight: 'bold' }}>{pred.ev}</div>
          </div>
        ))}
        
        <div style={{ textAlign: 'center', paddingTop: '2rem' }}>
          <button style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px dashed var(--text-secondary)', padding: '0.75rem 1.5rem', borderRadius: '4px', cursor: 'pointer', fontFamily: 'monospace' }}>
            Load Historical Archive
          </button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
