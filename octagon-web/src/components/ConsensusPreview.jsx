export default function ConsensusPreview() {
  const jsonPreview = `{
  "bout_id": "ufc314_001",
  "weight_class": "Featherweight",
  "fighter_a": {
    "name": "Alexander Volkanovski",
    "record": "26-4-0",
    "style": "Pressure Striker",
    "form_state": "Neutral",
    "win_probability": 0.61
  },
  "fighter_b": {
    "name": "Diego Lopes",
    "record": "24-5-0",
    "style": "Counter Striker",
    "form_state": "Hot",
    "win_probability": 0.39
  },
  "council_consensus": {
    "predicted_winner": "Alexander Volkanovski",
    "blended_win_prob": 0.61,
    "confidence_tier": "MEDIUM",
    "method_of_victory": {
      "KO_TKO": 0.28,
      "Submission": 0.07,
      "Decision": 0.65
    },
    ...
  }
}`;

  return (
    <section className="digest-preview">
      <div className="container grid-cols-2">
        <div style={{ alignSelf: 'center' }}>
          <span className="hero-subtitle">DATA OUTPUT</span>
          <h2 className="section-title heading-serif">Octagon Digest API</h2>
          <p className="hero-desc">
            Raw historical data flows through surface-specific models into the Council of Prophets. The final resolution is surfaced into a clean JSON digest—perfect for backtesting or triggering your local paper-trading daemons.
          </p>
          <div style={{ marginTop: '2rem' }}>
            <button className="btn-secondary">View API Docs</button>
          </div>
        </div>
        
        <div className="json-block text-mono">
          <pre>
            <code style={{ lineHeight: '1.8' }}>
              <span className="json-string">{jsonPreview}</span>
            </code>
          </pre>
        </div>
      </div>
    </section>
  );
}
