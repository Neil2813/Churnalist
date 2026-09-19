import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
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
    <div className="min-h-screen bg-paper text-ink">
      
      {/* Top Border */}
      <div style={{ borderTop: '1px solid var(--color-ink)', width: '100%' }}></div>

      {/* Main Header Row 1 */}
      <header className="w-full flex items-center justify-between" style={{ padding: '1rem 2rem', maxWidth: '100%' }}>
        {/* Logo Left */}
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 text-ink" style={{ textDecoration: 'none' }}>
            <img src="/Logo.png" alt="Churnalist Logo" style={{ height: '70px', width: 'auto', objectFit: 'contain' }} />
            <div>
              <h1 className="m-0" style={{ fontFamily: 'var(--font-logo)', fontSize: '3.5rem', marginBottom: 0, lineHeight: 1, fontWeight: 'bold', textTransform: 'none' }}>Churnalist</h1>
            </div>
          </Link>
        </div>

        {/* Nav Right */}
        <div className="flex items-center gap-6">
          <nav className="nav-links font-ui font-semibold text-sm flex items-center gap-6">
            <Link to="/" className="text-ink" style={{ borderBottom: '2px solid var(--color-ink)', paddingBottom: '0.25rem' }}>{t.investigate}</Link>
            <Link to="/stories" className="text-ink">{t.stories}</Link>
            <div style={{ width: '20px', height: '20px' }} />
          </nav>
          <div style={{ borderLeft: '1px solid var(--color-border)', paddingLeft: '1.5rem', height: '50px', display: 'flex', alignItems: 'center' }}>
            <p className="font-display" style={{ fontSize: '0.75rem', lineHeight: '1.2' }}>
              {t.tagline.split('.').filter(Boolean).map((chunk, idx) => (
                <span key={idx}>{chunk.trim()}{idx === 0 ? '.' : ''}<br/></span>
              ))}
            </p>
          </div>
        </div>
      </header>

      {/* Main Header Row 2 */}
      <div style={{ borderTop: '1px solid var(--color-ink)', borderBottom: '1px solid var(--color-ink)' }}>
        <div className="w-full top-bar" style={{ border: 'none', padding: '0.5rem 2rem', background: 'transparent', maxWidth: '100%', display: 'flex' }}>
          <span style={{ flex: 1, textAlign: 'left', fontFamily: 'var(--font-mono)' }}>{t.topBarLeft}</span>
          <span style={{ flex: 1, textAlign: 'center', fontFamily: 'var(--font-mono)' }}>{currentDate}</span>
          <span style={{ flex: 1, textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{t.topBarRight}</span>
        </div>
      </div>

      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/investigate/:eventId" element={<Investigation />} />
          <Route path="/stories" element={<Stories />} />
          <Route path="/provenance/:eventId" element={<Provenance />} />
        </Routes>
      </main>

      <div className="w-full border-top">
        <footer className="w-full flex justify-center py-8">
          <div className="flex flex-col items-center justify-center gap-1">
            <img src="/Logo.png" alt="Churnalist Logo" style={{ height: '32px' }} />
            <h2 className="m-0" style={{ fontFamily: 'var(--font-logo)', fontSize: '1.25rem', marginBottom: 0, fontWeight: 'bold', textTransform: 'none' }}>Churnalist</h2>
          </div>
        </footer>
      </div>
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
