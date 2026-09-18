import React, { useState, useEffect } from 'react';
import { 
  ArrowRight, Link as LinkIcon, Loader2, RotateCcw, 
  Sparkles, Cpu, CheckCircle2, Clock, GitCompare, Flame, 
  ShieldCheck, ExternalLink, Globe 
} from 'lucide-react';
import { api } from '../api';
import type { EventDetailResponse, ReportResponse } from '../api';
import { Link } from 'react-router-dom';

const SkeletonItem = ({ isMain = false }: { isMain?: boolean }) => (
  <div className={`newspaper-article ${isMain ? 'main-story border-0' : ''}`}>
    {!isMain && (
      <div className="news-meta">
        <div className="animate-pulse h-3 w-16" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse h-3 w-24" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
      </div>
    )}
    
    {isMain ? (
      <>
        <div className="animate-pulse h-10 w-3/4 mx-auto mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse h-10 w-1/2 mx-auto mb-6" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse w-full h-64 mb-4" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="news-meta justify-center mt-4">
          <div className="animate-pulse h-3 w-16" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
          <div className="animate-pulse h-3 w-24" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        </div>
        <div className="animate-pulse h-4 w-1/4 mx-auto mb-4" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse h-4 w-full mx-auto mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse h-4 w-5/6 mx-auto mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse h-4 w-4/5 mx-auto mb-6" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="flex justify-center mt-6">
          <div className="animate-pulse h-10 w-48" style={{ border: '2px solid var(--color-ink)', opacity: 0.1 }} />
        </div>
      </>
    ) : (
      <>
        <div className="animate-pulse h-6 w-full mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse h-6 w-3/4 mb-4" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        
        <div className="animate-pulse h-3 w-1/3 mb-3" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse h-3 w-full mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse h-3 w-5/6 mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        <div className="animate-pulse h-3 w-4/5 mb-4" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
        
        <div className="animate-pulse h-3 w-24" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.2 }} />
      </>
    )}
  </div>
);

const SkeletonCenterSecondary = () => (
  <div className="newspaper-article border-0 pb-0">
    <div className="animate-pulse h-8 w-3/4 mx-auto mb-4" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
    <div className="animate-pulse h-3 w-1/4 mx-auto mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
    <div className="animate-pulse h-3 w-full mx-auto mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
    <div className="animate-pulse h-3 w-5/6 mx-auto mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
  </div>
);

export default function Home() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newsArticles, setNewsArticles] = useState<any[]>([]);
  const [loadingNews, setLoadingNews] = useState(true);

  // In-place investigation states
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [investigatedEvent, setInvestigatedEvent] = useState<EventDetailResponse | null>(null);
  const [investigatedReport, setInvestigatedReport] = useState<ReportResponse | null>(null);
  const [loadingReport, setLoadingReport] = useState(false);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const top = await api.getTopNews();
        setNewsArticles(top || []);
      } catch (err) {
        console.error("Failed to load top news:", err);
      } finally {
        setLoadingNews(false);
      }
    };
    fetchNews();
  }, []);

  const handleTrace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setIsInvestigating(true);
    setInvestigatedEvent(null);
    setInvestigatedReport(null);

    try {
      const isUrl = query.startsWith('http');
      const ev = await api.discoverEvent(isUrl ? '' : query, isUrl ? query : undefined);
      
      // Fetch full event details with articles in-place
      const evDetail = await api.getEvent(ev.id);
      setInvestigatedEvent(evDetail);

      // Trigger Groq AI report in-place
      setLoadingReport(true);
      const rpt = await api.triggerAnalysis(ev.id).catch(() => api.getReport(ev.id).catch(() => null));
      if (rpt) setInvestigatedReport(rpt);
    } catch (err: any) {
      setError(err.message || 'An error occurred during discovery.');
    } finally {
      setLoading(false);
      setLoadingReport(false);
    }
  };

  // Helper to map investigated articles to newspaper layout format
  const transformArticle = (art: any, isMain = false) => ({
    id: art.id || Math.random().toString(),
    category: (art.language || "EN").toUpperCase(),
    date: art.published_at ? new Date(art.published_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }).toUpperCase() : "TODAY",
    title: art.title || "Untitled Article",
    excerpt: art.content ? (art.content.slice(0, 200) + "...") : "Discovered source article covering this news event.",
    source: art.source_name || "Live News Source",
    link: art.url || "#",
    imageUrl: isMain ? "https://images.openai.com/static-rsc-4/yfR8vPBESFSSsvbi4mJU8PpZgnAh1CdFgAaDsyiK0VYy768KbX4OoQP-w-0xufTt6Q6uhwalI-yd6Nfwyl5EAtSar0qSaDhDJkiiVWCKGyXaK0VJCvLW280Pyowk7T0kAGbhD-vsoJ2yvJp6pEH1956xStkPz5N2zYjMu5ZE__LOaJTBU9aotfXFMMYuknFy?purpose=fullsize" : undefined
  });

  const displayArticles = (isInvestigating && investigatedEvent?.articles && investigatedEvent.articles.length > 0)
    ? investigatedEvent.articles.map((a, idx) => transformArticle(a, idx === 0))
    : newsArticles;

  const showLoadingState = loadingNews || (isInvestigating && loading);

  return (
    <div className="flex flex-col w-full pb-16">
      
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
      <section className="mb-8 w-full">
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

      {/* 3-Column Newspaper Layout Grid (Default vs Searched URL result) */}
      <section className="mb-12 w-full min-h-[400px]">
        {showLoadingState ? (
          <div className="newspaper-layout" style={{ padding: '2rem' }}>
            <div className="newspaper-col-left">
              {[1, 2, 3].map(i => <SkeletonItem key={i} />)}
            </div>
            <div className="newspaper-col-center">
              <SkeletonItem isMain={true} />
              <hr style={{ borderTop: '2px solid var(--color-ink)', margin: '2.5rem 0 1.5rem', opacity: 0.2 }} />
              <SkeletonCenterSecondary />
            </div>
            <div className="newspaper-col-right">
              {[1, 2, 3].map(i => <SkeletonItem key={i} />)}
            </div>
          </div>
        ) : (
          <div className="newspaper-layout" style={{ padding: '2rem' }}>
            
            {/* Left Column */}
            <div className="newspaper-col-left">
              {displayArticles.slice(1, 4).map(article => (
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
                  <a href={article.link} target="_blank" rel="noopener noreferrer" className="trace-link text-blue text-xs font-bold font-mono inline-flex items-center gap-1">
                    READ ARTICLE <ExternalLink size={12}/>
                  </a>
                </div>
              ))}
            </div>

            {/* Center Column (Main Story) */}
            <div className="newspaper-col-center">
              {displayArticles.slice(0, 1).map(article => (
                <div key={article.id} className="newspaper-article main-story border-0">
                  <h3 className="font-display" style={{ fontSize: '3rem', lineHeight: '1.1', marginBottom: '1.5rem', textAlign: 'center' }}>
                    {article.title}
                  </h3>
                  {article.imageUrl && (
                    <img src={article.imageUrl} alt={article.title} className="news-image news-main-image" style={{ filter: 'grayscale(100%) contrast(1.2)' }} />
                  )}
                  <div className="news-meta justify-center mt-4">
                    <span>{article.category}</span>
                    <span className="date">{article.date}</span>
                  </div>
                  <div className="font-ui text-lg mb-4">
                    <span className="font-bold mr-2">By {article.source}</span>
                    <div className="excerpt mt-2" style={{ color: 'var(--color-ink)' }}>{article.excerpt}</div>
                  </div>
                  <div className="flex justify-center mt-6">
                    <a href={article.link} target="_blank" rel="noopener noreferrer" className="trace-link text-blue font-bold font-mono border border-blue px-6 py-2" style={{ border: '2px solid var(--color-blue)' }}>READ MAIN SOURCE</a>
                  </div>
                </div>
              ))}
              
              {displayArticles.length > 4 && (
                <>
                  <hr style={{ borderTop: '2px solid var(--color-ink)', margin: '2.5rem 0 1.5rem', opacity: 0.2 }} />
                  
                  {displayArticles.slice(4, 5).map(article => (
                    <div key={article.id} className="newspaper-article border-0 pb-0">
                      <h3 className="font-display" style={{ fontSize: '2rem', lineHeight: '1.1', marginBottom: '1rem', textAlign: 'center' }}>{article.title}</h3>
                      <div className="font-ui text-md mb-4 text-center">
                        <span className="font-bold mr-2">By {article.source}</span>
                        <span className="text-muted">{article.excerpt}</span>
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>

            {/* Right Column */}
            <div className="newspaper-col-right">
              {displayArticles.slice(5).map(article => (
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
                  <a href={article.link} target="_blank" rel="noopener noreferrer" className="trace-link text-blue text-xs font-bold font-mono inline-flex items-center gap-1">
                    READ ARTICLE <ExternalLink size={12}/>
                  </a>
                </div>
              ))}
            </div>

          </div>
        )}
      </section>

      {/* Groq AI Detailed Analysis Section (Rendered when URL search is performed) */}
      {isInvestigating && (
        <section className="px-8 mb-12 w-full fade-in pt-8" style={{ borderTop: '3px double var(--color-ink)' }}>
          <div className="flex flex-wrap justify-between items-center mb-6 gap-4">
            <div className="flex items-center gap-3">
              <div className="bg-ink text-paper p-2.5 flex items-center justify-center">
                <Sparkles size={22} className="text-amber-400" />
              </div>
              <div>
                <span className="font-mono text-xs text-muted uppercase tracking-wider block font-bold">GROQ AI ENGINE</span>
                <h3 className="font-display text-2xl md:text-3xl m-0">DETAILED AI PROVENANCE & TRUTH ANALYSIS</h3>
              </div>
            </div>
            {investigatedReport && (
              <div className="flex items-center gap-2 bg-paper border-all px-3 py-1.5 text-xs font-mono">
                <Cpu size={14} className="text-blue" />
                <span className="font-bold">CONFIDENCE SCORE: {(investigatedReport.confidence_score * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>

          {loadingReport && !investigatedReport ? (
            <div className="p-12 border-all border-dashed text-center font-mono text-muted flex flex-col items-center justify-center gap-3 bg-paper">
              <Loader2 size={24} className="animate-spin text-ink" />
              <span className="font-bold text-ink">GROQ LLM IS REASONING OVER ALL SOURCE ARTICLES...</span>
              <span className="text-xs">Analyzing accuracy, original publisher, claim changes, and churnalism values.</span>
            </div>
          ) : investigatedReport ? (
            <div className="flex flex-col gap-6">
              {/* Executive Summary */}
              <div className="bg-paper border-all p-6 shadow-sm">
                <span className="font-mono text-xs bg-ink text-paper px-2 py-0.5 uppercase mb-2 inline-block font-bold">EXECUTIVE SUMMARY</span>
                <h4 className="font-display text-xl mb-2">{investigatedReport.headline}</h4>
                <p className="font-ui text-md leading-relaxed text-ink mb-0">{investigatedReport.summary}</p>
              </div>

              {/* 4 Deep Insights Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* 1. Accuracy & Truth Assessment */}
                <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #10b981' }}>
                  <div className="flex items-center gap-2 text-emerald-700 font-mono font-bold text-xs uppercase mb-3">
                    <CheckCircle2 size={18} /> ACCURACY & TRUTH ASSESSMENT
                  </div>
                  <p className="font-ui text-sm text-ink leading-relaxed m-0">
                    {investigatedReport.accuracy_analysis || "Core factual claims maintain strong evidence consistency across primary coverage."}
                  </p>
                </div>

                {/* 2. First Publisher / Origin */}
                <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #3b82f6' }}>
                  <div className="flex items-center gap-2 text-blue font-mono font-bold text-xs uppercase mb-3">
                    <Clock size={18} /> FIRST PUBLISHER & ORIGIN
                  </div>
                  <div className="font-ui text-sm">
                    <span className="font-bold text-ink block mb-1">
                      Published First By: <span className="text-blue font-mono">{investigatedReport.first_publisher || "Primary Publisher"}</span>
                    </span>
                    {investigatedReport.first_published_at && (
                      <span className="font-mono text-xs text-muted block">
                        Original Timestamp: {investigatedReport.first_published_at}
                      </span>
                    )}
                  </div>
                </div>

                {/* 3. Changed / Modified Claims */}
                <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #f59e0b' }}>
                  <div className="flex items-center gap-2 text-amber-700 font-mono font-bold text-xs uppercase mb-3">
                    <GitCompare size={18} /> CLAIM TRANSFORMATIONS & DRIFT
                  </div>
                  <p className="font-ui text-sm text-ink leading-relaxed m-0">
                    {investigatedReport.key_drifts && investigatedReport.key_drifts.length > 0 
                      ? `${investigatedReport.key_drifts.length} claim modifications identified across editions (e.g., ${investigatedReport.key_drifts[0].explanation}).`
                      : "No significant claim modifications or numerical alterations detected across compared article versions."}
                  </p>
                </div>

                {/* 4. Churnalism & Fake / Exaggerated Values */}
                <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #ef4444' }}>
                  <div className="flex items-center gap-2 text-red-700 font-mono font-bold text-xs uppercase mb-3">
                    <Flame size={18} /> CHURNALISM & SENSATIONAL VALUES
                  </div>
                  <p className="font-ui text-sm text-ink leading-relaxed m-0">
                    {investigatedReport.churn_analysis || "Content replication analysis complete."}
                  </p>
                </div>
              </div>

              {/* Reader Takeaway */}
              {investigatedReport.reader_takeaway && (
                <div className="border-all p-5 bg-paper flex items-start gap-3 shadow-sm">
                  <ShieldCheck size={22} className="text-blue flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-mono text-xs font-bold uppercase text-muted block mb-1">VERIFICATION TAKEAWAY FOR READERS</span>
                    <p className="font-ui text-sm text-ink m-0 font-medium leading-relaxed">{investigatedReport.reader_takeaway}</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-8 border-all text-center text-muted font-mono text-sm bg-paper">
              Detailed AI analysis complete.
            </div>
          )}
        </section>
      )}

    </div>
  );
}


