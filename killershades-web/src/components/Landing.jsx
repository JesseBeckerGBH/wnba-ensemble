import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Server, Activity } from 'lucide-react';

const Landing = () => {
  const navigate = useNavigate();
  const [deliveryMethod, setDeliveryMethod] = useState('API');

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-core)', color: 'var(--text-primary)', overflowY: 'auto', fontFamily: "'Inter', sans-serif" }}>
      
      {/* Top Nav */}
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem 4rem', borderBottom: '1px solid var(--border-light)' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', letterSpacing: '4px', color: 'var(--accent-brand)', fontWeight: 900 }}>KILLERSHADES</h1>
        <button 
          onClick={() => navigate('/dashboard')}
          style={{ background: 'transparent', color: 'white', border: '1px solid var(--border-light)', padding: '0.75rem 2rem', borderRadius: '4px', cursor: 'pointer', fontFamily: 'monospace', letterSpacing: '1px' }}
        >
          Terminal Login //
        </button>
      </nav>

      {/* Hero Section */}
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '8rem 2rem', textAlign: 'center' }}>
        <h2 style={{ fontSize: '4.5rem', fontWeight: 900, letterSpacing: '-2px', marginBottom: '1.5rem', textTransform: 'uppercase', lineHeight: 1.1 }}>
          The Most Asymmetric<br /> <span style={{ color: 'var(--accent-positive)' }}>Sports Betting Model Ensembles.</span>
        </h2>
        <p style={{ fontSize: '1.25rem', color: 'var(--text-secondary)', maxWidth: '900px', margin: '0 auto 4rem auto', lineHeight: 1.6 }}>
          Our Model Ensembles are so unique they systematically trick the SportsBooks. We don't just sell picks. We sell isolated intelligence. Get your predictions delivered however and whenever you want, or lease the raw model to run exactly how it suits You.
        </p>

        <button 
          onClick={() => navigate('/dashboard')}
          style={{ fontSize: '1.25rem', padding: '1.25rem 4rem', background: 'var(--accent-positive)', color: '#000', border: 'none', borderRadius: '4px', fontWeight: 900, cursor: 'pointer', letterSpacing: '2px', textTransform: 'uppercase', boxShadow: '0 0 20px rgba(185, 28, 28, 0.3)' }}
        >
          LEASE THE ENSEMBLE
        </button>
      </main>

      {/* Customization Floor */}
      <section style={{ backgroundColor: 'var(--bg-panel)', padding: '6rem 2rem', borderTop: '1px solid var(--border-light)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h3 style={{ fontSize: '2rem', textAlign: 'center', marginBottom: '4rem', letterSpacing: '1px', color: 'var(--text-primary)' }}>CONFIGURE YOUR ARCHITECTURE</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'revert', gap: '4rem' }}>
            {/* Using inline media queries is tricky in raw JSX without styled-components, assuming standard desktop flow for the blueprint */}
            <div style={{ display: 'flex', gap: '4rem', flexDirection: 'row' }}>
              
              {/* Delivery Toggle (Left Side) */}
              <div style={{ flex: 1, backgroundColor: 'var(--bg-core)', padding: '2.5rem', borderRadius: '4px', border: '1px solid var(--border-light)' }}>
                <h4 style={{ margin: '0 0 2rem 0', color: 'var(--text-secondary)', fontFamily: 'monospace', letterSpacing: '1px' }}>1. SELECT DELIVERY PIPELINE</h4>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <button 
                    onClick={() => setDeliveryMethod('API')}
                    style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', padding: '1.5rem', background: deliveryMethod === 'API' ? 'rgba(185, 28, 28, 0.15)' : 'transparent', border: deliveryMethod === 'API' ? '1px solid var(--accent-positive)' : '1px solid var(--border-light)', color: 'white', textAlign: 'left', cursor: 'pointer', borderRadius: '4px' }}
                  >
                    <Server size={32} color={deliveryMethod === 'API' ? 'var(--accent-positive)' : 'var(--text-secondary)'}/>
                    <div>
                      <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Direct Server Integration</h5>
                      <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>Pipe True EV milliseconds before market correction straight to your trading bots.</p>
                    </div>
                  </button>

                  <button 
                    onClick={() => setDeliveryMethod('DASHBOARD')}
                    style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', padding: '1.5rem', background: deliveryMethod === 'DASHBOARD' ? 'rgba(234, 179, 8, 0.1)' : 'transparent', border: deliveryMethod === 'DASHBOARD' ? '1px solid var(--accent-brand)' : '1px solid var(--border-light)', color: 'white', textAlign: 'left', cursor: 'pointer', borderRadius: '4px' }}
                  >
                    <Activity size={32} color={deliveryMethod === 'DASHBOARD' ? 'var(--accent-brand)' : 'var(--text-secondary)'}/>
                    <div>
                      <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>Bloomberg-Style Web Terminal</h5>
                      <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>Login manually and monitor the Matrix visually via our secure browser platform.</p>
                    </div>
                  </button>
                </div>
              </div>

              {/* Tech Specs (Right Side) */}
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <h4 style={{ margin: '0 0 1rem 0', fontSize: '2rem', color: 'var(--text-primary)', letterSpacing: '-1px' }}>Absolute Flexibility.</h4>
                <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', lineHeight: 1.7, marginBottom: '3rem' }}>
                  Whether you're running a massive proprietary script betting thousands of micro-transactions, or you just want 5 rock-solid Stochastic Consensus predictions pinged to your Telegram daily—our structural nodes bend completely to your workflow.
                </p>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                  <div style={{ padding: '1.5rem', borderTop: '3px solid var(--accent-positive)', backgroundColor: 'var(--bg-core)' }}>
                    <h5 style={{ margin: '0 0 0.75rem 0', fontSize: '1.5rem' }}>&lt; 300ms</h5>
                    <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>Kafka-powered response latency to react against sharp syndicate manipulation.</p>
                  </div>
                  <div style={{ padding: '1.5rem', borderTop: '3px solid var(--accent-brand)', backgroundColor: 'var(--bg-core)' }}>
                    <h5 style={{ margin: '0 0 0.75rem 0', fontSize: '1.5rem' }}>10x Agents</h5>
                    <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>Parallelized LLM triangulations systematically bypassing square public hype.</p>
                  </div>
                </div>
              </div>
            </div>
            
          </div>
        </div>
      </section>
    </div>
  );
};

export default Landing;
