import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Target, BarChart3, Trophy, Shield, Gauge } from 'lucide-react';
import RoadRunnerLogo from '../components/RoadRunnerLogo';

const TIERS = [
  {
    name: 'Street',
    price: '$9.99',
    period: '/mo',
    desc: 'Daily picks for the casual bettor.',
    color: '#A8A8A8',
    features: [
      'Moneyline picks (3+ per night)',
      'Model confidence scores',
      'Basic edge readout',
      'Daily email alerts',
    ],
    icon: <Gauge size={28} />,
    slug: 'street',
  },
  {
    name: 'Track',
    price: '$29.99',
    period: '/mo',
    desc: 'Full cockpit access — see what the engine sees.',
    color: '#FF6B00',
    featured: true,
    features: [
      'Everything in Street',
      'Totals picks (O/U)',
      'Live tachometer dashboard',
      'Kelly sizing recommendations',
      'Paper trading history',
      'Performance dyno charts',
    ],
    icon: <Target size={28} />,
    slug: 'track',
  },
  {
    name: 'Strip',
    price: '$49.99',
    period: '/mo',
    desc: 'Full throttle. Institutional-grade analytics.',
    color: '#39FF14',
    features: [
      'Everything in Track',
      'Spreads + alt lines',
      'ONNX model access (API)',
      'Custom Kelly fraction tuning',
      'Slack/Discord alerts',
      'Priority model retraining',
      'Early access to new sports',
    ],
    icon: <Trophy size={28} />,
    slug: 'strip',
  },
];

export default function Garage() {
  const navigate = useNavigate();

  return (
    <div className="vinyl-dash" style={{ minHeight: '100vh' }}>
      {/* ── Hero Section ──────────────────────────────────────────────── */}
      <header
        style={{
          textAlign: 'center',
          padding: '4rem 1.5rem 3rem',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Subtle orange glow behind logo */}
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -60%)',
            width: '400px',
            height: '400px',
            background: 'radial-gradient(circle, rgba(255,107,0,0.08) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />

        <RoadRunnerLogo size={140} />

        <h1
          style={{
            fontFamily: "'Russo One', sans-serif",
            fontSize: 'clamp(2.2rem, 5vw, 3.8rem)',
            color: '#FF6B00',
            marginTop: '1rem',
            textShadow: '0 0 30px rgba(255,107,0,0.3)',
            letterSpacing: '0.04em',
          }}
        >
          ROADRUNNER
        </h1>

        <p
          style={{
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: 'clamp(0.9rem, 2vw, 1.2rem)',
            color: '#39FF14',
            marginTop: '0.3rem',
            textShadow: '0 0 10px rgba(57,255,20,0.3)',
            letterSpacing: '0.15em',
          }}
        >
          NBA ENSEMBLE SPORTS BETTING MODEL ENGINE
        </p>

        <p
          style={{
            fontFamily: "'Oswald', sans-serif",
            fontSize: '0.85rem',
            color: '#666',
            marginTop: '1rem',
            maxWidth: '600px',
            marginLeft: 'auto',
            marginRight: 'auto',
            letterSpacing: '0.05em',
          }}
        >
          LogisticRegression + XGBoost + LightGBM stacked ensemble
          <br />
          Calibrated probabilities · Kelly criterion sizing · 24/7 paper trading
        </p>

        {/* Engine spec badges */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '1.5rem',
            marginTop: '2rem',
            flexWrap: 'wrap',
          }}
        >
          {[
            { icon: '🏀', label: '30 Teams', sub: 'Full NBA' },
            { icon: '🧠', label: '3-Model Stack', sub: 'LR+XGB+LGB' },
            { icon: '⚡', label: 'ONNX Runtime', sub: '<5ms inference' },
            { icon: '📊', label: 'Paper Trading', sub: '24/7 live tracking' },
          ].map((spec) => (
            <div
              key={spec.label}
              style={{
                background: '#1A1A1A',
                border: '1px solid #333',
                borderRadius: '8px',
                padding: '0.8rem 1.2rem',
                minWidth: '120px',
              }}
            >
              <div style={{ fontSize: '1.5rem' }}>{spec.icon}</div>
              <div
                style={{
                  fontFamily: "'Oswald', sans-serif",
                  fontWeight: 600,
                  fontSize: '0.85rem',
                  color: '#F0F0E8',
                  marginTop: '0.3rem',
                }}
              >
                {spec.label}
              </div>
              <div
                style={{
                  fontFamily: "'Share Tech Mono', monospace",
                  fontSize: '0.65rem',
                  color: '#666',
                }}
              >
                {spec.sub}
              </div>
            </div>
          ))}
        </div>
      </header>

      {/* ── Tier Cards ────────────────────────────────────────────────── */}
      <section
        style={{
          maxWidth: '1100px',
          margin: '0 auto',
          padding: '2rem 1.5rem 4rem',
        }}
      >
        <h2
          style={{
            fontFamily: "'Oswald', sans-serif",
            fontWeight: 700,
            fontSize: '1.4rem',
            textAlign: 'center',
            color: '#FF6B00',
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            marginBottom: '2rem',
          }}
        >
          Choose Your Ride
        </h2>

        <div
          className="tier-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '1.5rem',
            alignItems: 'start',
          }}
        >
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`tier-card ${tier.featured ? 'featured' : ''}`}
              style={{
                transform: tier.featured ? 'scale(1.03)' : 'none',
              }}
            >
              {tier.featured && (
                <div
                  style={{
                    position: 'absolute',
                    top: '12px',
                    right: '12px',
                    background: '#FF6B00',
                    color: '#0D0D0D',
                    fontSize: '0.6rem',
                    fontFamily: "'Oswald', sans-serif",
                    fontWeight: 700,
                    letterSpacing: '0.1em',
                    padding: '0.2rem 0.6rem',
                    borderRadius: '4px',
                  }}
                >
                  MOST POPULAR
                </div>
              )}

              <div style={{ color: tier.color, marginBottom: '0.5rem' }}>
                {tier.icon}
              </div>

              <h3
                style={{
                  fontFamily: "'Russo One', sans-serif",
                  fontSize: '1.5rem',
                  color: tier.color,
                  letterSpacing: '0.06em',
                }}
              >
                {tier.name}
              </h3>

              <div style={{ marginTop: '0.3rem', marginBottom: '0.8rem' }}>
                <span
                  style={{
                    fontFamily: "'Oswald', sans-serif",
                    fontSize: '2.4rem',
                    fontWeight: 700,
                    color: '#F0F0E8',
                  }}
                >
                  {tier.price}
                </span>
                <span style={{ color: '#666', fontSize: '0.85rem' }}>
                  {tier.period}
                </span>
              </div>

              <p style={{ color: '#888', fontSize: '0.8rem', marginBottom: '1.2rem' }}>
                {tier.desc}
              </p>

              <ul style={{ listStyle: 'none', marginBottom: '1.5rem' }}>
                {tier.features.map((f) => (
                  <li
                    key={f}
                    style={{
                      fontSize: '0.8rem',
                      color: '#CCC',
                      padding: '0.3rem 0',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.5rem',
                    }}
                  >
                    <span style={{ color: '#39FF14', fontSize: '0.7rem', marginTop: '0.15rem' }}>
                      ✓
                    </span>
                    {f}
                  </li>
                ))}
              </ul>

              <button
                className={tier.featured ? 'rev-btn' : 'chrome-btn'}
                style={{ width: '100%' }}
                onClick={() => navigate(`/cockpit/${tier.slug}`)}
              >
                {tier.featured ? '🏁 Start Engine' : 'Select'}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────── */}
      <footer
        style={{
          textAlign: 'center',
          padding: '2rem 1rem',
          borderTop: '1px solid #222',
          color: '#444',
          fontSize: '0.7rem',
          fontFamily: "'Share Tech Mono', monospace",
        }}
      >
        <div style={{ color: '#FF6B00', fontSize: '0.75rem', marginBottom: '0.5rem' }}>
          ROADRUNNER NBA · JB Analytics LLC
        </div>
        <div>
          Powered by stacked ensemble ML · ONNX Runtime · Rust Kelly Engine · C++ Execution Layer
        </div>
        <div style={{ marginTop: '0.3rem' }}>
          <Shield size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
          Paper trading mode — no real money at risk
        </div>
      </footer>
    </div>
  );
}
