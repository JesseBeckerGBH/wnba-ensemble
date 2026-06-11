export default function StatsCounters() {
  const stats = [
    { label: "FIGHTS ANALYZED", value: "7,422" },
    { label: "MARKOV STATES", value: "86,412" },
    { label: "YEARS OF DATA", value: "31" },
    { label: "COUNCIL RESOLUTION", value: "14 MS" }
  ];

  return (
    <section>
      <div className="container">
        <div className="stats-grid">
          {stats.map((s, idx) => (
            <div key={idx} className="stat-item" style={{ textAlign: 'center' }}>
              <div className="stat-value text-mono">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
