import React, { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, Activity, TrendingUp, Zap, Clock, DollarSign,
  Target, BarChart3, AlertTriangle, CheckCircle,
} from 'lucide-react';
import TachGauge from '../components/TachGauge';
import MuscleDash from '../components/MuscleDash';
import BetSheet from '../components/BetSheet';
import PerfChart from '../components/PerfChart';
import RoadRunnerLogo from '../components/RoadRunnerLogo';
import useTelemetry from '../hooks/useTelemetry';

/**
 * RoadRunnerCockpit — Main NBA dashboard.
 * Feels like sitting behind the wheel of a 1971 Plymouth RoadRunner.
 * Gauge cluster shows live model telemetry, bet sheet shows today's action.
 */
export default function RoadRunnerCockpit() {
  const navigate = useNavigate();
  const { tier } = useParams();
  const telemetry = useTelemetry();
  const [revving, setRevving] = useState(false);
  const [lastBet, setLastBet] = useState(null);

  const handleRevEngine = useCallback((bet) => {
    setRevving(true);
    setLastBet(bet);
    // Reset after animation
    setTimeout(() => setRevving(false), 1200);
  }, []);

  // Status color mapping
  const statusColors = {
    IDLE: '#666',
    SCANNING: '#FF6B00',
    EDGE_FOUND: '#39FF14',
    EXECUTING: '#FFD700',
  };

  return (
    <div className="vinyl-dash" style={{ minHeight: '100vh' }}>
      {/* ── Top Bar ───────────────────────────────────────────────────── */}
      <nav
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.6rem 1.2rem',
          background: '#111',
          borderBottom: '2px solid #222',
        }}
      >
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'none',
            border: 'none',
            color: '#A8A8A8',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            fontFamily: "'Oswald', sans-serif",
            fontSize: '0.8rem',
            letterSpacing: '0.06em',
          }}
        >
          <ArrowLeft size={16} /> GARAGE
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
          <RoadRunnerLogo size={32} />
          <span
            style={{
              fontFamily: "'Russo One', sans-serif",
              fontSize: '1.1rem',
              color: '#FF6B00',
              letterSpacing: '0.04em',
            }}
          >
            ROADRUNNER
          </span>
          {tier && (
            <span
              style={{
                fontFamily: "'Oswald', sans-serif",
                fontSize: '0.7rem',
                color: '#39FF14',
                background: 'rgba(57,255,20,0.1)',
                padding: '0.15rem 0.5rem',
                borderRadius: '4px',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
              }}
            >
              {tier}
            </span>
          )}
        </div>

        {/* Engine status indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: '0.75rem',
          }}
        >
          <div
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: statusColors[telemetry.status] || '#666',
              boxShadow: `0 0 6px ${statusColors[telemetry.status] || '#666'}`,
              animation: telemetry.status === 'SCANNING' ? 'redline-pulse 1s infinite' : 'none',
            }}
          />
          <span style={{ color: statusColors[telemetry.status] || '#666' }}>
            {telemetry.status}
          </span>
        </div>
      </nav>

      {/* ── Main Content ──────────────────────────────────────────────── */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '0.5rem' }}>
        {/* ── Gauge Cluster Row ─────────────────────────────────────────── */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'flex-start',
            gap: '0.5rem',
            flexWrap: 'wrap',
            padding: '1rem 0',
          }}
        >
          <TachGauge
            value={telemetry.winProb}
            label="Win Prob"
            displayValue={`${telemetry.winProb.toFixed(1)}%`}
            size={170}
            redlineStart={75}
            revving={revving}
          />
          <TachGauge
            value={telemetry.edge * 10}
            label="Edge"
            displayValue={`${telemetry.edge.toFixed(1)}%`}
            size={200}
            redlineStart={70}
            revving={revving}
          />
          <TachGauge
            value={telemetry.auc * 100}
            label="Model AUC"
            displayValue={telemetry.auc.toFixed(3)}
            size={170}
            redlineStart={85}
          />
        </div>

        {/* ── Stats Strip ──────────────────────────────────────────────── */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '1rem',
            flexWrap: 'wrap',
            marginBottom: '0.5rem',
          }}
        >
          {[
            {
              icon: <DollarSign size={14} />,
              label: 'BANKROLL',
              value: `$${telemetry.bankroll.toLocaleString()}`,
              color: telemetry.bankroll >= 10000 ? '#39FF14' : '#FF1A1A',
            },
            {
              icon: <Target size={14} />,
              label: 'BETS TODAY',
              value: telemetry.betsToday,
              color: '#FF6B00',
            },
            {
              icon: <TrendingUp size={14} />,
              label: 'WIN RATE',
              value: `${telemetry.winRate.toFixed(1)}%`,
              color: telemetry.winRate >= 55 ? '#39FF14' : '#FFAA00',
            },
            {
              icon: <Clock size={14} />,
              label: 'LAST SCAN',
              value: telemetry.lastScan || '—',
              color: '#A8A8A8',
            },
          ].map((stat) => (
            <div
              key={stat.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                background: '#111',
                border: '1px solid #2A2A2A',
                borderRadius: '6px',
                padding: '0.4rem 0.8rem',
              }}
            >
              <span style={{ color: '#666' }}>{stat.icon}</span>
              <div>
                <div
                  style={{
                    fontSize: '0.55rem',
                    color: '#666',
                    fontFamily: "'Oswald', sans-serif",
                    letterSpacing: '0.1em',
                  }}
                >
                  {stat.label}
                </div>
                <div
                  className="digital-readout"
                  style={{ fontSize: '0.9rem', color: stat.color }}
                >
                  {stat.value}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* ── Active Pick Banner ─────────────────────────────────────────── */}
        {telemetry.activePick && (
          <div
            style={{
              textAlign: 'center',
              padding: '0.5rem',
              margin: '0.5rem 0.75rem',
              background: 'rgba(255, 107, 0, 0.08)',
              border: '1px solid rgba(255, 107, 0, 0.3)',
              borderRadius: '8px',
            }}
          >
            <span style={{ color: '#FF6B00', fontSize: '0.7rem', fontFamily: "'Oswald', sans-serif", letterSpacing: '0.1em' }}>
              <Zap size={12} style={{ verticalAlign: 'middle' }} /> ACTIVE TARGET:{' '}
            </span>
            <span className="digital-readout" style={{ fontSize: '1rem' }}>
              {telemetry.activePick}
            </span>
          </div>
        )}

        {/* ── Dashboard Grid ──────────────────────────────────────────── */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0',
          }}
        >
          {/* Bet Sheet */}
          <div style={{ gridColumn: 'span 2' }}>
            <MuscleDash title="Tonight's Action" icon="🏁">
              <BetSheet onRevEngine={handleRevEngine} />
            </MuscleDash>
          </div>

          {/* Performance Chart */}
          <div style={{ gridColumn: 'span 2' }}>
            <MuscleDash title="Dyno Chart — Paper Trading P&L" icon="📈">
              <PerfChart />
            </MuscleDash>
          </div>

          {/* Model Info */}
          <MuscleDash title="Engine Specs" icon="🔧">
            <div style={{ fontSize: '0.8rem', lineHeight: '1.8' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Architecture</span>
                <span className="digital-readout">LR+XGB+LGB Stack</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Calibration</span>
                <span className="digital-readout">Isotonic CV</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Inference</span>
                <span className="digital-readout">ONNX Runtime</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Sizing</span>
                <span className="digital-readout">Quarter Kelly</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Min Prob Gate</span>
                <span className="digital-readout">55.0%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>AUC Gate</span>
                <span className="digital-readout">0.580</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Execution</span>
                <span className="digital-readout">Rust + C++</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Mode</span>
                <span style={{
                  color: '#FFD700',
                  fontFamily: "'Share Tech Mono', monospace",
                  textShadow: '0 0 6px rgba(255,215,0,0.3)',
                }}>
                  PAPER TRADING
                </span>
              </div>
            </div>
          </MuscleDash>

          {/* Model Version / Status */}
          <MuscleDash title="Model Status" icon="🏎️">
            <div style={{ fontSize: '0.8rem', lineHeight: '1.8' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>ML Model</span>
                <span style={{ color: '#39FF14', fontFamily: "'Share Tech Mono', monospace" }}>
                  <CheckCircle size={12} style={{ verticalAlign: 'middle' }} /> LOADED
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Totals Model</span>
                <span style={{ color: '#39FF14', fontFamily: "'Share Tech Mono', monospace" }}>
                  <CheckCircle size={12} style={{ verticalAlign: 'middle' }} /> LOADED
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>ONNX Export</span>
                <span style={{ color: '#39FF14', fontFamily: "'Share Tech Mono', monospace" }}>
                  <CheckCircle size={12} style={{ verticalAlign: 'middle' }} /> READY
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Rust Engine</span>
                <span style={{ color: '#FFAA00', fontFamily: "'Share Tech Mono', monospace" }}>
                  <AlertTriangle size={12} style={{ verticalAlign: 'middle' }} /> STANDBY
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>C++ Exec</span>
                <span style={{ color: '#FFAA00', fontFamily: "'Share Tech Mono', monospace" }}>
                  <AlertTriangle size={12} style={{ verticalAlign: 'middle' }} /> STANDBY
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>Odds Feed</span>
                <span style={{ color: '#39FF14', fontFamily: "'Share Tech Mono', monospace" }}>
                  <Activity size={12} style={{ verticalAlign: 'middle' }} /> CONNECTED
                </span>
              </div>
              <div style={{ marginTop: '0.8rem' }}>
                <span style={{ color: '#666', fontSize: '0.7rem' }}>
                  Sport: basketball_nba · Region: us,uk,eu · Poll: 3600s
                </span>
              </div>
            </div>
          </MuscleDash>
        </div>
      </div>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer
        style={{
          textAlign: 'center',
          padding: '1.5rem',
          borderTop: '1px solid #222',
          color: '#444',
          fontSize: '0.65rem',
          fontFamily: "'Share Tech Mono', monospace",
        }}
      >
        ROADRUNNER NBA · JB Analytics LLC · beep beep 🏎️💨
      </footer>
    </div>
  );
}
