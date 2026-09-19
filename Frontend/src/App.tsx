import { BrowserRouter, Routes, Route, Link, NavLink } from 'react-router-dom';
import Home from './pages/Home';
import Investigation from './pages/Investigation';
import Stories from './pages/Stories';
import Provenance from './pages/Provenance';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import './index.css';
import './App.css'; 

function AppContent() {
  const { t } = useLanguage();
  const currentDate = new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).toUpperCase();

  return (
    <div className="min-h-screen flex flex-col bg-paper text-ink" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Main Header */}
      <header className="w-full flex items-center justify-between" style={{ padding: '1rem 2rem', maxWidth: '100%', borderTop: '1px solid var(--color-ink)', borderBottom: '1px solid var(--color-ink)', position: 'relative' }}>
        {/* Logo Left */}
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 text-ink" style={{ textDecoration: 'none' }}>
            <img src="/Logo.png" alt="Churnalist Logo" style={{ height: '70px', width: 'auto', objectFit: 'contain' }} />
            <div>
              <h1 className="m-0" style={{ fontFamily: 'var(--font-logo)', fontSize: '3.5rem', marginBottom: 0, lineHeight: 1, fontWeight: 'bold', textTransform: 'none' }}>Churnalist</h1>
            </div>
          </Link>
        </div>

        {/* Center Nav */}
        <nav className="nav-center-menu">
          <NavLink 
            to="/" 
            end
            className={({ isActive }) => `nav-link-item ${isActive ? 'active' : ''}`}
          >
            {t.investigate}
          </NavLink>
          <span className="nav-divider">|</span>
          <NavLink 
            to="/stories" 
            className={({ isActive }) => `nav-link-item ${isActive ? 'active' : ''}`}
          >
            {t.stories}
          </NavLink>
        </nav>

        {/* Right Section: Date & Slogan */}
        <div className="flex items-center gap-4">
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 500, letterSpacing: '0.05em', marginRight: '0.5rem' }}>
            {currentDate}
          </span>
          <div style={{ borderLeft: '1px solid var(--color-border)', paddingLeft: '1.5rem', height: '50px', display: 'flex', alignItems: 'center' }}>
            <p className="font-display" style={{ fontSize: '0.75rem', lineHeight: '1.2' }}>
              {t.tagline.split('.').filter(Boolean).map((chunk, idx) => (
                <span key={idx}>{chunk.trim()}{idx === 0 ? '.' : ''}<br/></span>
              ))}
            </p>
          </div>
        </div>
      </header>

      <main className="flex-1 w-full" style={{ flex: '1 0 auto' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/investigate/:eventId" element={<Investigation />} />
          <Route path="/stories" element={<Stories />} />
          <Route path="/provenance/:eventId" element={<Provenance />} />
        </Routes>
      </main>

      <footer aria-label="Churnalist footer" style={{ borderTop: '1px solid var(--color-ink)', borderBottom: '1px solid var(--color-ink)', marginTop: 'auto', padding: '1.25rem 2rem', flexShrink: 0 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) auto minmax(0, 1fr)', alignItems: 'center', width: '100%' }}>
          <p className="font-mono" style={{ margin: 0, fontSize: '0.7rem', letterSpacing: '0.12em', color: 'var(--color-muted)' }}>
            {t.topBarLeft}
          </p>
          <Link to="/" aria-label="Churnalist home" className="flex items-center gap-1 text-ink" style={{ textDecoration: 'none', justifySelf: 'center', color: 'var(--color-ink)' }}>
            <img src="/Logo.png" alt="" style={{ height: '32px', width: 'auto', objectFit: 'contain' }} />
            <span style={{ fontFamily: 'var(--font-logo)', fontSize: '1.75rem', lineHeight: 1, fontWeight: 'bold', color: 'var(--color-ink)' }}>Churnalist</span>
          </Link>
          <p className="font-mono" style={{ margin: 0, fontSize: '0.7rem', letterSpacing: '0.12em', color: 'var(--color-muted)', textAlign: 'right' }}>
            {t.topBarRight}
          </p>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AppContent />
      </LanguageProvider>
    </BrowserRouter>
  );
}

export default App;
