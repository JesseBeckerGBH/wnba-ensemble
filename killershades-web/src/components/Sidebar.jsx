import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldAlert, BarChart2, Zap, CreditCard, Crosshair, Cpu } from 'lucide-react';

const Sidebar = ({ activeTier, setActiveTier }) => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const getNavStyle = (path) => ({
    display: 'flex', alignItems: 'center', gap: '0.75rem', 
    background: location.pathname === path ? 'rgba(185, 28, 28, 0.15)' : 'transparent', 
    color: location.pathname === path ? 'var(--text-primary)' : 'var(--text-secondary)', 
    border: location.pathname === path ? '1px solid var(--accent-positive)' : '1px solid transparent',
    textAlign: 'left', cursor: 'pointer', padding: '0.75rem', borderRadius: '4px'
  });

  return (
    <div style={{ borderRight: '1px solid var(--border-light)', backgroundColor: 'var(--bg-core)', padding: '2rem 1.5rem', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '4rem' }}>
        <h1 style={{ margin: 0, fontSize: '1.25rem', letterSpacing: '3px', color: 'var(--accent-brand)' }}>KILLERSHADES</h1>
        <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', letterSpacing: '1px' }}>SYNDICATE TERMINAL v1.0</span>
      </div>

      <nav style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <button className="nav-btn" onClick={() => navigate('/dashboard')} style={getNavStyle('/dashboard')}>
          <BarChart2 size={18} color="var(--text-secondary)" /> System Terminal
        </button>
        <button className="nav-btn" onClick={() => navigate('/dashboard/beast-v2')} style={getNavStyle('/dashboard/beast-v2')}>
          <Cpu size={18} color={location.pathname === '/dashboard/beast-v2' ? 'var(--accent-positive)' : 'var(--text-secondary)'} /> BEAST v2
        </button>
        <button className="nav-btn" onClick={() => navigate('/dashboard/darts-v2')} style={getNavStyle('/dashboard/darts-v2')}>
          <Crosshair size={18} color={location.pathname === '/dashboard/darts-v2' ? 'var(--accent-positive)' : 'var(--text-secondary)'} /> DARTS v2
        </button>
      </nav>

      <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '1.5rem' }}>
        <p style={{ margin: '0 0 1rem 0', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>SUBSCRIPTION TIER</p>
        <select 
          value={activeTier}
          onChange={(e) => setActiveTier(e.target.value)}
          style={{ width: '100%', padding: '0.75rem', background: 'var(--bg-panel)', color: 'var(--text-primary)', border: '1px solid var(--border-light)', fontFamily: 'monospace', borderRadius: '4px' }}
        >
          <option value="CORE">CORE ($49/mo)</option>
          <option value="PRO">PRO ($199/mo)</option>
          <option value="WHALE">WHALE ($999/mo)</option>
        </select>
        
        <button style={{ marginTop: '1rem', width: '100%', padding: '0.75rem', background: 'white', color: 'black', border: 'none', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
          <CreditCard size={16} /> Upgrade / Stripe
        </button>
      </div>
    </div>
  );
}

export default Sidebar;
