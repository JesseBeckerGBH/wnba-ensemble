export default function CouncilArchitecture() {
  const prophets = [
    { id: "P1", name: "Bayesian Fighter Model", desc: "Posterior win probability distributions using historical priors, updating strictly on fight outcomes." },
    { id: "P2", name: "LSTM Sequence Model", desc: "Recurrent sequences analyzing striking trajectories, finish rates, and form momentum over the last N fights." },
    { id: "P3", name: "XGBoost Ensemble Predictor", desc: "Differential tabular matrices comparing reach, age, and style matchups across 7,422 historical UFC bouts." },
    { id: "P4", name: "42,318-State Markov Chain", desc: "Form transition modeling. Evaluates probabilities of a fighter transitioning from Hot -> Declining, adjusting baseline metrics." },
    { id: "P5", name: "Sharp Money Signal", desc: "Continuous ingestion of closing line values and line movement velocity to detect professional steam alignment." },
  ];

  return (
    <section style={{ padding: '5rem 0' }}>
      <div className="container">
        <div style={{ marginBottom: '2rem' }}>
          <span className="hero-subtitle">SYSTEM ARCHITECTURE</span>
          <h2 className="section-title heading-serif">The Council of Prophets</h2>
          <p className="hero-desc" style={{ marginBottom: 0 }}>
            The Octagon operates as a parallel multi-model pipeline. Each Prophet assesses the fight from a distinct mathematical perspective before the Orchestrator blends a final prediction.
          </p>
        </div>

        <div className="architecture-grid">
          {prophets.map((p) => (
            <div key={p.id} className="glass-card prophet-node">
              <div className="prophet-badge text-mono">{p.id}</div>
              <div className="prophet-content">
                <h4>{p.name}</h4>
                <p>{p.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
