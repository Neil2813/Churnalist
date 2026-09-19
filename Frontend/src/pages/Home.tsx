import React, { useState, useEffect } from 'react';
import { 
  ArrowRight, Link as LinkIcon, Loader2, 
  Sparkles, Cpu, CheckCircle2, Clock, GitCompare, Flame, 
  ShieldCheck, ExternalLink, Languages 
} from 'lucide-react';
import { api } from '../api';
import type { EventDetailResponse, ReportResponse, ArticleTranslationResponse } from '../api';
import { useLanguage } from '../context/LanguageContext';
import type { SupportedLanguage } from '../utils/uiTranslations';

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

const SUPPORTED_TRANSLATION_LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi (हिन्दी)' },
  { code: 'ta', name: 'Tamil (தமிழ்)' },
  { code: 'te', name: 'Telugu (తెలుగు)' },
  { code: 'bn', name: 'Bengali (বাংলা)' },
  { code: 'kn', name: 'Kannada (ಕನ್ನಡ)' },
];

export default function Home() {
  const { t, language, setLanguage } = useLanguage();
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

  // Full article translation on read states
  const [selectedLanguage, setSelectedLanguage] = useState<string>(language);
  const [translation, setTranslation] = useState<ArticleTranslationResponse | null>(null);
  const [translating, setTranslating] = useState<boolean>(false);
  const [translationError, setTranslationError] = useState<string | null>(null);
  const [showOriginal, setShowOriginal] = useState<boolean>(false);
  const [sidebarTranslations, setSidebarTranslations] = useState<Record<string, ArticleTranslationResponse>>({});
  const [translatingSidebarIds, setTranslatingSidebarIds] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setSelectedLanguage(language);
  }, [language]);

  // Helper to map investigated articles to newspaper layout format
  const transformArticle = (art: any, isMain = false) => ({
    id: art.id || Math.random().toString(),
    category: (art.language || "EN").toUpperCase(),
    language: art.language || "en",
    date: art.published_at ? new Date(art.published_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }).toUpperCase() : t.today,
    title: art.title || "Untitled Article",
    excerpt: art.content ? (art.content.slice(0, 200) + "...") : "Discovered source article covering this news event.",
    content: art.content,
    source: art.source_name || "Live News Source",
    link: art.url || "#",
    imageUrl: isMain ? "https://images.openai.com/static-rsc-4/yfR8vPBESFSSsvbi4mJU8PpZgnAh1CdFgAaDsyiK0VYy768KbX4OoQP-w-0xufTt6Q6uhwalI-yd6Nfwyl5EAtSar0qSaDhDJkiiVWCKGyXaK0VJCvLW280Pyowk7T0kAGbhD-vsoJ2yvJp6pEH1956xStkPz5N2zYjMu5ZE__LOaJTBU9aotfXFMMYuknFy?purpose=fullsize" : undefined
  });

  const displayArticles = (isInvestigating && investigatedEvent?.articles && investigatedEvent.articles.length > 0)
    ? investigatedEvent.articles.map((a, idx) => transformArticle(a, idx === 0))
    : newsArticles;

  const triggerTranslation = async (articleId: string, lang: string, articlesList?: any[]) => {
    if (!articleId) return;
    setSelectedLanguage(lang);
    setLanguage(lang as SupportedLanguage);
    setTranslating(true);
    setTranslationError(null);
    setShowOriginal(false);

    // 1. Translate main story first so user gets the main article immediately
    const mainPromise = (async () => {
      try {
        const data = await api.translateArticle(articleId, lang, false);
        setTranslation(data);
      } catch (err: any) {
        setTranslationError(err.message || 'Translation failed, please try again');
      } finally {
        setTranslating(false);
      }
    })();

    // 2. Translate all visible sidebar cards (headline + excerpt) in parallel
    const articles = (articlesList && articlesList.length > 0) ? articlesList : displayArticles;
    const sidebarArticles = articles.slice(1, 8).filter((a: any) => a.id && a.id !== articleId);

    const sidebarPromises = sidebarArticles.map(async (art: any) => {
      setTranslatingSidebarIds(prev => ({ ...prev, [art.id]: true }));
      try {
        const data = await api.translateArticle(art.id, lang, true);
        setSidebarTranslations(prev => ({ ...prev, [art.id]: data }));
      } catch (err) {
        console.warn(`Sidebar translation failed for article ${art.id}:`, err);
      } finally {
        setTranslatingSidebarIds(prev => ({ ...prev, [art.id]: false }));
      }
    });

    await Promise.allSettled([mainPromise, ...sidebarPromises]);
  };

  const handleTranslate = async (articleId: string, lang: string) => {
    await triggerTranslation(articleId, lang);
  };

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
    setTranslation(null);
    setTranslationError(null);
    setShowOriginal(false);
    setSidebarTranslations({});
    setTranslatingSidebarIds({});

    try {
      const isUrl = query.startsWith('http');
      const ev = await api.discoverEvent(isUrl ? '' : query, isUrl ? query : undefined);
      
      // Fetch full event details with articles in-place
      const evDetail = await api.getEvent(ev.id);
      setInvestigatedEvent(evDetail);

      // Automatically translate entire UI when URL is traced
      if (evDetail.articles && evDetail.articles.length > 0) {
        const mainArt = evDetail.articles[0];
        const formattedArticles = evDetail.articles.map((a: any, idx: number) => transformArticle(a, idx === 0));
        triggerTranslation(mainArt.id, selectedLanguage, formattedArticles);
      }

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

  const showLoadingState = loadingNews || (isInvestigating && loading);

  return (
    <div className="flex flex-col w-full pb-16">
      
      {/* Hero Section */}
      <section className="mb-4 w-full">
        <div className="w-full" style={{ display: 'grid', gridTemplateColumns: '10% 80% 10%', padding: '2.5rem 2rem 1rem', alignItems: 'center' }}>
          
          {/* Left Column */}
          <div style={{ borderRight: '1px solid var(--color-border)', paddingRight: '2rem', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <p className="font-display" style={{ fontStyle: 'italic', fontSize: '1.25rem', marginBottom: '1rem' }}>
              {t.heroQuote}
            </p>
            <span className="font-ui text-sm uppercase font-semibold text-muted">{t.heroAuthor}</span>
          </div>
          
          {/* Center Column */}
          <div style={{ textAlign: 'center', padding: '0 3rem' }}>
            <h2 className="font-display" style={{ fontSize: '3.5vw', margin: '0 auto', lineHeight: 1.1 }}>
              {t.heroHeadline}
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
              {t.heroSide}
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
              <span className="font-mono text-muted uppercase" style={{ fontSize: '0.65rem', letterSpacing: '0.1em', marginBottom: '0.25rem' }}>{t.investigate}</span>
              <h2 className="font-display m-0" style={{ fontSize: '1.75rem', lineHeight: '1' }}>{t.tagline}</h2>
            </div>
          </div>
          
          {/* Middle: Italic Text */}
          <div className="flex-shrink-0" style={{ borderLeft: '1px solid var(--color-border)', paddingLeft: '2rem', height: '40px', display: 'flex', alignItems: 'center' }}>
            <span className="font-display text-muted" style={{ fontStyle: 'italic', fontSize: '1.1rem' }}>{t.heroQuote}</span>
          </div>

          {/* Right: Search Box */}
          <div className="flex-1" style={{ maxWidth: '400px' }}>
            <form onSubmit={handleTrace} className="search-container flex items-center" style={{ margin: 0, width: '100%', boxShadow: 'none', borderRadius: 0, padding: 0, height: '45px', border: '1px solid var(--color-border)' }}>
              <div className="search-input-wrapper flex-1 flex items-center" style={{ paddingLeft: '1rem', borderRight: 'none', height: '100%' }}>
                <LinkIcon size={16} className="text-muted mr-2" />
                <input 
                  type="text" 
                  placeholder={t.searchPlaceholder} 
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  disabled={loading}
                  style={{ fontSize: '0.9rem', width: '100%', border: 'none', background: 'transparent', outline: 'none' }}
                />
              </div>
              <button type="submit" className="search-btn flex items-center justify-center gap-2" disabled={loading} style={{ fontWeight: 'bold', borderRadius: 0, padding: '0 1.5rem', height: '100%', backgroundColor: 'var(--color-ink)', color: 'var(--color-paper)' }}>
                {loading ? t.tracingBtn : t.traceBtn} <ArrowRight size={16} />
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
              {displayArticles.slice(1, 4).map(article => {
                const sidebarTrans = sidebarTranslations[article.id];
                const isSidebarTranslating = Boolean(translatingSidebarIds[article.id]);
                const activeTitle = (sidebarTrans && !showOriginal)
                  ? (sidebarTrans.translated_title || article.title)
                  : article.title;
                const activeExcerpt = (sidebarTrans && !showOriginal && sidebarTrans.translated_content)
                  ? (sidebarTrans.translated_content.slice(0, 200) + '...')
                  : article.excerpt;
                const isTranslated = Boolean(sidebarTrans && !showOriginal);

                return (
                  <div key={article.id} className="newspaper-article">
                    <div className="news-meta">
                      <span>{isTranslated ? sidebarTrans.target_language.toUpperCase() : article.category}</span>
                      <span className="date">{article.date}</span>
                      {isSidebarTranslating && (
                        <span className="inline-flex items-center gap-1 text-[10px] text-blue font-mono font-bold animate-pulse">
                          <Loader2 size={10} className="animate-spin" /> TRANSLATING...
                        </span>
                      )}
                    </div>
                    <h3 className="font-display text-xl mb-2">{activeTitle}</h3>
                    <div className="font-ui text-sm mb-4">
                      <span className="font-bold mr-2">{t.by} {article.source}</span>
                      <span className="text-muted">{activeExcerpt}</span>
                    </div>
                    <a href={article.link} target="_blank" rel="noopener noreferrer" className="trace-link text-blue text-xs font-bold font-mono inline-flex items-center gap-1">
                      {t.readArticle} <ExternalLink size={12}/>
                    </a>
                  </div>
                );
              })}
            </div>

            {/* Center Column (Main Story) */}
            <div className="newspaper-col-center">
              {displayArticles.slice(0, 1).map(article => {
                const isCurrentTranslation = Boolean(translation && translation.article_id === article.id);
                const activeTitle = (isCurrentTranslation && !showOriginal)
                  ? (translation?.translated_title || article.title)
                  : article.title;
                const activeContent = (isCurrentTranslation && !showOriginal)
                  ? (translation?.translated_content || article.content || article.excerpt)
                  : (article.content || article.excerpt);
                const isTranslatedView = isCurrentTranslation && !showOriginal;

                return (
                  <div key={article.id} className="newspaper-article main-story border-0">
                    
                    {/* Translation Control Panel (URL-paste translation on read) */}
                    {isInvestigating && (
                      <div className="w-full bg-paper border-all p-3 mb-6 shadow-sm">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <Languages size={18} className="text-blue" />
                            <span className="font-mono text-xs font-bold uppercase tracking-wider">
                              {t.translateFullArticle}
                            </span>
                          </div>

                          <div className="flex items-center gap-2 flex-wrap">
                            <select
                              value={selectedLanguage}
                              onChange={(e) => {
                                setSelectedLanguage(e.target.value);
                                handleTranslate(article.id, e.target.value);
                              }}
                              disabled={translating}
                              className="font-mono text-xs border border-ink bg-white px-2.5 py-1.5 cursor-pointer outline-none font-semibold"
                            >
                              {SUPPORTED_TRANSLATION_LANGUAGES.map(l => (
                                <option key={l.code} value={l.code}>{l.name}</option>
                              ))}
                            </select>

                            <button
                              type="button"
                              onClick={() => handleTranslate(article.id, selectedLanguage)}
                              disabled={translating}
                              className="font-mono text-xs px-3 py-1.5 uppercase font-bold flex items-center gap-1.5"
                            >
                              {translating ? (
                                <>
                                  <Loader2 size={12} className="animate-spin" /> {t.translatingBtn}
                                </>
                              ) : (
                                t.translateBtn
                              )}
                            </button>

                            {isCurrentTranslation && (
                              <button
                                type="button"
                                onClick={() => setShowOriginal(!showOriginal)}
                                className="outline font-mono text-xs px-3 py-1.5 uppercase font-bold flex items-center gap-1"
                                style={{ border: '1px solid var(--color-ink)' }}
                              >
                                {showOriginal ? t.viewTranslation : t.viewOriginal}
                              </button>
                            )}
                          </div>
                        </div>

                        {translationError && (
                          <div className="mt-2 text-alert font-mono text-xs">
                            <strong>Translation Error:</strong> {translationError}
                          </div>
                        )}

                        {isCurrentTranslation && translation && (
                          <div className="mt-3 pt-2 border-top flex items-center justify-between font-mono text-xs text-muted flex-wrap gap-2">
                            <span>
                              {isTranslatedView ? (
                                <>
                                  {t.translatedFrom} <strong className="text-ink uppercase">{translation.original_language_name || translation.original_language}</strong> {t.into} <strong className="text-blue uppercase">{translation.target_language_name}</strong>
                                </>
                              ) : (
                                <>
                                  {t.viewingOriginal} (<strong className="text-ink uppercase">{translation.original_language_name || translation.original_language}</strong>)
                                </>
                              )}
                            </span>
                            {translation.cached && (
                              <span className="bg-ink text-paper px-1.5 py-0.5 text-[10px] font-bold uppercase">
                                {t.fromCache}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    <h3 className="font-display" style={{ fontSize: '3rem', lineHeight: '1.1', marginBottom: '1.5rem', textAlign: 'center' }}>
                      {activeTitle}
                    </h3>
                    {article.imageUrl && (
                      <img src={article.imageUrl} alt={activeTitle} className="news-image news-main-image" style={{ filter: 'grayscale(100%) contrast(1.2)' }} />
                    )}
                    <div className="news-meta justify-center mt-4">
                      <span>{isTranslatedView && translation ? translation.target_language.toUpperCase() : article.category}</span>
                      <span className="date">{article.date}</span>
                    </div>
                    
                    <div className="font-ui text-base mb-6 mt-4">
                      <div className="font-bold mb-3">{t.by} {article.source}</div>
                      <div className="leading-relaxed space-y-4" style={{ color: 'var(--color-ink)' }}>
                        {activeContent.split(/\n\s*\n/).filter(Boolean).map((para: string, pIdx: number) => (
                          <p key={pIdx} className="mb-3 text-justify">{para.trim()}</p>
                        ))}
                      </div>
                    </div>

                    <div className="flex justify-center mt-6">
                      <a href={article.link} target="_blank" rel="noopener noreferrer" className="trace-link text-blue font-bold font-mono border border-blue px-6 py-2" style={{ border: '2px solid var(--color-blue)' }}>{t.readMainSource}</a>
                    </div>
                  </div>
                );
              })}
              
              {displayArticles.length > 4 && (
                <>
                  <hr style={{ borderTop: '2px solid var(--color-ink)', margin: '2.5rem 0 1.5rem', opacity: 0.2 }} />
                  
                  {displayArticles.slice(4, 5).map(article => {
                    const sidebarTrans = sidebarTranslations[article.id];
                    const isSidebarTranslating = Boolean(translatingSidebarIds[article.id]);
                    const activeTitle = (sidebarTrans && !showOriginal)
                      ? (sidebarTrans.translated_title || article.title)
                      : article.title;
                    const activeExcerpt = (sidebarTrans && !showOriginal && sidebarTrans.translated_content)
                      ? (sidebarTrans.translated_content.slice(0, 200) + '...')
                      : article.excerpt;
                    const isTranslated = Boolean(sidebarTrans && !showOriginal);

                    return (
                      <div key={article.id} className="newspaper-article border-0 pb-0">
                        <div className="news-meta justify-center mb-2">
                          <span>{isTranslated ? sidebarTrans.target_language.toUpperCase() : article.category}</span>
                          <span className="date">{article.date}</span>
                          {isSidebarTranslating && (
                            <span className="inline-flex items-center gap-1 text-[10px] text-blue font-mono font-bold animate-pulse ml-2">
                              <Loader2 size={10} className="animate-spin" /> TRANSLATING...
                            </span>
                          )}
                        </div>
                        <h3 className="font-display" style={{ fontSize: '2rem', lineHeight: '1.1', marginBottom: '1rem', textAlign: 'center' }}>{activeTitle}</h3>
                        <div className="font-ui text-md mb-4 text-center">
                          <span className="font-bold mr-2">{t.by} {article.source}</span>
                          <span className="text-muted">{activeExcerpt}</span>
                        </div>
                      </div>
                    );
                  })}
                </>
              )}
            </div>

            {/* Right Column */}
            <div className="newspaper-col-right">
              {displayArticles.slice(5).map(article => {
                const sidebarTrans = sidebarTranslations[article.id];
                const isSidebarTranslating = Boolean(translatingSidebarIds[article.id]);
                const activeTitle = (sidebarTrans && !showOriginal)
                  ? (sidebarTrans.translated_title || article.title)
                  : article.title;
                const activeExcerpt = (sidebarTrans && !showOriginal && sidebarTrans.translated_content)
                  ? (sidebarTrans.translated_content.slice(0, 200) + '...')
                  : article.excerpt;
                const isTranslated = Boolean(sidebarTrans && !showOriginal);

                return (
                  <div key={article.id} className="newspaper-article">
                    <div className="news-meta">
                      <span>{isTranslated ? sidebarTrans.target_language.toUpperCase() : article.category}</span>
                      <span className="date">{article.date}</span>
                      {isSidebarTranslating && (
                        <span className="inline-flex items-center gap-1 text-[10px] text-blue font-mono font-bold animate-pulse">
                          <Loader2 size={10} className="animate-spin" /> {t.translatingCard}
                        </span>
                      )}
                    </div>
                    <h3 className="font-display text-xl mb-2">{activeTitle}</h3>
                    <div className="font-ui text-sm mb-4">
                      <span className="font-bold mr-2">{t.by} {article.source}</span>
                      <span className="text-muted">{activeExcerpt}</span>
                    </div>
                    <a href={article.link} target="_blank" rel="noopener noreferrer" className="trace-link text-blue text-xs font-bold font-mono inline-flex items-center gap-1">
                      {t.readArticle} <ExternalLink size={12}/>
                    </a>
                  </div>
                );
              })}
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
                <h3 className="font-display text-2xl md:text-3xl m-0">{t.analysisTitle}</h3>
              </div>
            </div>
            {investigatedReport && (
              <div className="flex items-center gap-2 bg-paper border-all px-3 py-1.5 text-xs font-mono">
                <Cpu size={14} className="text-blue" />
                <span className="font-bold">{t.confidenceScore}: {(investigatedReport.confidence_score * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>

          {loadingReport && !investigatedReport ? (
            <div className="p-12 border-all border-dashed text-center font-mono text-muted flex flex-col items-center justify-center gap-3 bg-paper">
              <Loader2 size={24} className="animate-spin text-ink" />
              <span className="font-bold text-ink">{t.analyzingReport}</span>
            </div>
          ) : investigatedReport ? (
            <div className="flex flex-col gap-6">
              {/* Executive Summary */}
              <div className="bg-paper border-all p-6 shadow-sm">
                <span className="font-mono text-xs bg-ink text-paper px-2 py-0.5 uppercase mb-2 inline-block font-bold">{t.summaryTitle}</span>
                <h4 className="font-display text-xl mb-2">{investigatedReport.headline}</h4>
                <p className="font-ui text-md leading-relaxed text-ink mb-0">{investigatedReport.summary}</p>
              </div>

              {/* 4 Deep Insights Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* 1. Accuracy & Truth Assessment */}
                <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #10b981' }}>
                  <div className="flex items-center gap-2 text-emerald-700 font-mono font-bold text-xs uppercase mb-3">
                    <CheckCircle2 size={18} /> {t.sourcesTitle}
                  </div>
                  <p className="font-ui text-sm text-ink leading-relaxed m-0">
                    {investigatedReport.accuracy_analysis || "Core factual claims maintain strong evidence consistency across primary coverage."}
                  </p>
                </div>

                {/* 2. First Publisher / Origin */}
                <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #3b82f6' }}>
                  <div className="flex items-center gap-2 text-blue font-mono font-bold text-xs uppercase mb-3">
                    <Clock size={18} /> {t.primarySource}
                  </div>
                  <div className="font-ui text-sm">
                    <span className="font-bold text-ink block mb-1">
                      {t.primarySource}: <span className="text-blue font-mono">{investigatedReport.first_publisher || "Primary Publisher"}</span>
                    </span>
                    {investigatedReport.first_published_at && (
                      <span className="font-mono text-xs text-muted block">
                        Timestamp: {investigatedReport.first_published_at}
                      </span>
                    )}
                  </div>
                </div>

                {/* 3. Changed / Modified Claims */}
                <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #f59e0b' }}>
                  <div className="flex items-center gap-2 text-amber-700 font-mono font-bold text-xs uppercase mb-3">
                    <GitCompare size={18} /> {t.driftTitle}
                  </div>
                  <p className="font-ui text-sm text-ink leading-relaxed m-0">
                    {investigatedReport.key_drifts && investigatedReport.key_drifts.length > 0 
                      ? `${investigatedReport.key_drifts.length} modifications identified (e.g., ${investigatedReport.key_drifts[0].explanation}).`
                      : t.noDrift}
                  </p>
                </div>

                {/* 4. Churnalism & Fake / Exaggerated Values */}
                <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #ef4444' }}>
                  <div className="flex items-center gap-2 text-red-700 font-mono font-bold text-xs uppercase mb-3">
                    <Flame size={18} /> {t.correctionsTitle}
                  </div>
                  <p className="font-ui text-sm text-ink leading-relaxed m-0">
                    {investigatedReport.churn_analysis || t.noCorrections}
                  </p>
                </div>
              </div>

              {/* Reader Takeaway */}
              {investigatedReport.reader_takeaway && (
                <div className="border-all p-5 bg-paper flex items-start gap-3 shadow-sm">
                  <ShieldCheck size={22} className="text-blue flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-mono text-xs font-bold uppercase text-muted block mb-1">{t.derivativeSource}</span>
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


