export default function Header() {
  return (
    <header style={{ padding: '2rem 0', borderBottom: '1px solid var(--card-border)' }}>
      <div className="container flex-between">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '32px', height: '32px', background: 'var(--color-accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 'bold', fontFamily: 'var(--font-mono)'
          }}>
            O
          </div>
          <span className="heading-serif" style={{ fontSize: '1.5rem', color: '#fff' }}>
            THE OCTAGON
          </span>
        </div>
        <nav style={{ display: 'flex', gap: '2rem' }}>
          <a href="#" style={{ color: 'var(--color-text-main)', textDecoration: 'none', fontSize: '0.9rem' }}>Architecture</a>
          <a href="#" style={{ color: 'var(--color-text-main)', textDecoration: 'none', fontSize: '0.9rem' }}>Backtesting</a>
          <a href="#" style={{ color: 'var(--color-text-main)', textDecoration: 'none', fontSize: '0.9rem' }}>Digest</a>
        </nav>
        <button className="btn-primary">Get Access</button>
      </div>
    </header>
  );
}
