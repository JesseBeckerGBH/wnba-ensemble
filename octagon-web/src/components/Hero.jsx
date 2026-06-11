export default function Hero() {
  return (
    <section className="hero">
      <div className="container">
        <span className="hero-subtitle">Algorithmic UFC Intelligence</span>
        <h1 className="hero-title heading-serif">
          The Octagon
        </h1>
        <p className="hero-desc">
          A self-annealing probability engine built on decades of historical UFC data. A multi-model ensemble (The Council of Prophets) runs 24/7 on dedicated Proxmox infrastructure, continuously predicting fight outcomes, edges, and sharp money alignments.
        </p>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="btn-primary">Subscribe Now</button>
          <button className="btn-secondary">Explore the Engine</button>
        </div>
      </div>
    </section>
  );
}
