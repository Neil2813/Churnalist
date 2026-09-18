import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Link as LinkIcon } from 'lucide-react';
import { api } from '../api';
import { newsArticles } from '../data';
import { Link } from 'react-router-dom';

export default function Home() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleTrace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const isUrl = query.startsWith('http');
      const ev = await api.discoverEvent(isUrl ? '' : query, isUrl ? query : undefined);
      navigate(`/investigate/${ev.id}`);
    } catch (err: any) {
      setError(err.message || 'An error occurred during discovery.');
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-full">
      
      {/* Hero Section */}
      <section className="mb-4 w-full">
        <div className="w-full" style={{ display: 'grid', gridTemplateColumns: '10% 80% 10%', padding: '2.5rem 2rem 1rem', alignItems: 'center' }}>
          
          {/* Left Column */}
          <div style={{ borderRight: '1px solid var(--color-border)', paddingRight: '2rem', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <p className="font-display" style={{ fontStyle: 'italic', fontSize: '1.25rem', marginBottom: '1rem' }}>
              "In a world of<br/>
              information, context<br/>
              is everything."
            </p>
            <span className="font-ui text-sm uppercase font-semibold text-muted">— CHURNALIST</span>
          </div>
          
          {/* Center Column */}
          <div style={{ textAlign: 'center', padding: '0 3rem' }}>
            <h2 className="font-display" style={{ fontSize: '3.5vw', margin: '0 auto', lineHeight: 1.1 }}>
              THE SAME STORY DOESN'T ALWAYS STAY THE SAME.
            </h2>

            {error && (
              <div className="bg-alert text-white p-4 w-full text-center font-mono mt-4">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>
          
          {/* Right Column */}
          <div style={{ borderLeft: '1px solid var(--color-border)', paddingLeft: '2rem', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <p className="font-mono text-muted uppercase" style={{ fontSize: '0.8rem', lineHeight: '1.5', letterSpacing: '0.1em' }}>
              PEOPLE READ<br/>
              NEWS. WE READ<br/>
              BETWEEN<br/>
              THE LINES.
            </p>
            <div style={{ width: '20px', height: '2px', backgroundColor: 'var(--color-ink)', marginTop: '1rem' }}></div>
          </div>
        </div>

        {/* Double border bottom */}
        <div style={{ borderBottom: '2px solid var(--color-ink)', width: '100%' }}></div>
        <div style={{ borderBottom: '1px solid var(--color-ink)', width: '100%', marginTop: '4px' }}></div>
      </section>

      {/* URL Input Section */}
      <section className="mb-12 w-full">
        {/* Double border top */}
        <div style={{ borderTop: '2px solid var(--color-ink)', width: '100%', marginBottom: '4px' }}></div>
        <div style={{ borderTop: '1px solid var(--color-ink)', width: '100%' }}></div>
        
        <div style={{ padding: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '2rem' }}>
          
          {/* Left: Mascot & Headline */}
          <div className="flex items-center gap-4 flex-shrink-0">
            <img src="/Investigate.png" alt="Investigate Mascot" style={{ height: '60px', width: 'auto', objectFit: 'contain' }} />
            <div className="flex flex-col">
              <span className="font-mono text-muted uppercase" style={{ fontSize: '0.65rem', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>INVESTIGATE A STORY</span>
              <h2 className="font-display m-0" style={{ fontSize: '1.75rem', lineHeight: '1' }}>PASTE A STORY TO INVESTIGATE</h2>
            </div>
          </div>
          
          {/* Middle: Italic Text */}
          <div className="flex-shrink-0" style={{ borderLeft: '1px solid var(--color-border)', paddingLeft: '2rem', height: '40px', display: 'flex', alignItems: 'center' }}>
            <span className="font-display text-muted" style={{ fontStyle: 'italic', fontSize: '1.1rem' }}>See how the same story<br/>changes across sources.</span>
          </div>

          {/* Right: Search Box */}
          <div className="flex-1" style={{ maxWidth: '400px' }}>
            <form onSubmit={handleTrace} className="search-container flex items-center" style={{ margin: 0, width: '100%', boxShadow: 'none', borderRadius: 0, padding: 0, height: '45px', border: '1px solid var(--color-border)' }}>
              <div className="search-input-wrapper flex-1 flex items-center" style={{ paddingLeft: '1rem', borderRight: 'none', height: '100%' }}>
                <LinkIcon size={16} className="text-muted mr-2" />
                <input 
                  type="text" 
                  placeholder="Enter URL of your news" 
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  disabled={loading}
                  style={{ fontSize: '0.9rem', width: '100%', border: 'none', background: 'transparent', outline: 'none' }}
                />
              </div>
              <button type="submit" className="search-btn flex items-center justify-center gap-2" disabled={loading} style={{ fontWeight: 'bold', borderRadius: 0, padding: '0 1.5rem', height: '100%', backgroundColor: 'var(--color-ink)', color: 'var(--color-paper)' }}>
                {loading ? 'TRACING...' : 'TRACE'} <ArrowRight size={16} />
              </button>
            </form>
          </div>


        </div>

        {/* Double border bottom */}
        <div style={{ borderBottom: '1px solid var(--color-ink)', width: '100%', marginBottom: '4px' }}></div>
        <div style={{ borderBottom: '2px solid var(--color-ink)', width: '100%' }}></div>
      </section>

      {/* Latest News Section (No Filters) */}
      <section className="mb-12 w-full">
        <div className="newspaper-layout" style={{ padding: '2rem' }}>
          
          {/* Left Column */}
          <div className="newspaper-col-left">
            {newsArticles.slice(1, 4).map(article => (
              <div key={article.id} className="newspaper-article">
                <div className="news-meta">
                  <span>{article.category}</span>
                  <span className="date">{article.date}</span>
                </div>
                <h3 className="font-display text-xl mb-2">{article.title}</h3>
                <div className="font-ui text-sm mb-4">
                  <span className="font-bold mr-2">By {article.source}</span>
                  <span className="text-muted">{article.excerpt}</span>
                </div>
                <Link to={article.link} className="trace-link text-blue text-xs font-bold font-mono">TRACE STORY <ArrowRight size={12}/></Link>
              </div>
            ))}
          </div>

          {/* Center Column */}
          <div className="newspaper-col-center">
            {newsArticles.slice(0, 1).map(article => (
              <div key={article.id} className="newspaper-article main-story border-0">
                <h3 className="font-display" style={{ fontSize: '3rem', lineHeight: '1.1', marginBottom: '1.5rem', textAlign: 'center' }}>
                  {article.title}
                </h3>
                <img src={article.imageUrl} alt={article.title} className="news-image news-main-image" style={{ filter: 'grayscale(100%) contrast(1.2)' }} />
                <div className="news-meta justify-center mt-4">
                  <span>{article.category}</span>
                  <span className="date">{article.date}</span>
                </div>
                <div className="font-ui text-lg mb-4">
                  <span className="font-bold mr-2">By {article.source}</span>
                  <div className="excerpt mt-2" style={{ color: 'var(--color-ink)' }}>{article.excerpt}</div>
                </div>
                <div className="flex justify-center mt-6">
                  <Link to={article.link} className="trace-link text-blue font-bold font-mono border border-blue px-6 py-2" style={{ border: '2px solid var(--color-blue)' }}>TRACE THIS STORY</Link>
                </div>
              </div>
            ))}
            
            <hr style={{ borderTop: '2px solid var(--color-ink)', margin: '2.5rem 0 1.5rem', opacity: 0.2 }} />
            
            {newsArticles.slice(4, 5).map(article => (
              <div key={article.id} className="newspaper-article border-0 pb-0">
                <h3 className="font-display" style={{ fontSize: '2rem', lineHeight: '1.1', marginBottom: '1rem', textAlign: 'center' }}>{article.title}</h3>
                <div className="font-ui text-md mb-4 text-center">
                  <span className="font-bold mr-2">By {article.source}</span>
                  <span className="text-muted">{article.excerpt}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Right Column */}
          <div className="newspaper-col-right">
            {newsArticles.slice(5).map(article => (
              <div key={article.id} className="newspaper-article">
                <div className="news-meta">
                  <span>{article.category}</span>
                  <span className="date">{article.date}</span>
                </div>
                <h3 className="font-display text-xl mb-2">{article.title}</h3>
                <div className="font-ui text-sm mb-4">
                  <span className="font-bold mr-2">By {article.source}</span>
                  <span className="text-muted">{article.excerpt}</span>
                </div>
                <Link to={article.link} className="trace-link text-blue text-xs font-bold font-mono">TRACE STORY <ArrowRight size={12}/></Link>
              </div>
            ))}
            

          </div>

        </div>
      </section>
      
    </div>
  );
}
