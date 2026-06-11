import Header from './components/Header'
import Hero from './components/Hero'
import StatsCounters from './components/StatsCounters'
import CouncilArchitecture from './components/CouncilArchitecture'
import ConsensusPreview from './components/ConsensusPreview'

function App() {
  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      <Header />
      <main>
        <Hero />
        <StatsCounters />
        <CouncilArchitecture />
        <ConsensusPreview />
      </main>
      
      <footer style={{ padding: '3rem 0', borderTop: '1px solid var(--card-border)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        <p className="text-mono" style={{ fontSize: '0.8rem' }}>THE OCTAGON © 2026. RUNNING ON PROXMOX VE.</p>
      </footer>
    </div>
  )
}

export default App
