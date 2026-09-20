import React, { useState, useEffect } from 'react';
import { 
  ArrowRight, Link as LinkIcon, Loader2, 
  ExternalLink 
} from 'lucide-react';
import { api } from '../api';
import type { EventDetailResponse, ReportResponse, ArticleTranslationResponse } from '../api';
import { useLanguage } from '../context/LanguageContext';
import type { SupportedLanguage } from '../utils/uiTranslations';
import { StoryVerificationReport } from '../components/StoryVerificationReport';

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

  const [translatedReport, setTranslatedReport] = useState<{
    headline?: string;
    summary?: string;
    accuracy?: string;
    publisher?: string;
    drifts?: string;
    churn?: string;
    takeaway?: string;
  } | null>(null);

  useEffect(() => {
    if (!investigatedReport) return;
    if (language === 'en') {
      setTranslatedReport(null);
      return;
    }
    let active = true;
    const translateReport = async () => {
      try {
        const [tHeadline, tSummary, tAccuracy, tPublisher, tDrifts, tChurn, tTakeaway] = await Promise.all([
          investigatedReport.headline ? api.translateText(investigatedReport.headline, language) : Promise.resolve(''),
          investigatedReport.summary ? api.translateText(investigatedReport.summary, language) : Promise.resolve(''),
          investigatedReport.accuracy_analysis ? api.translateText(investigatedReport.accuracy_analysis, language) : Promise.resolve(''),
          investigatedReport.first_publisher ? api.translateText(investigatedReport.first_publisher, language) : Promise.resolve(''),
          (investigatedReport.key_drifts && investigatedReport.key_drifts.length > 0) ? api.translateText(`${investigatedReport.key_drifts.length} story modifications identified across coverage.`, language) : Promise.resolve(''),
          investigatedReport.churn_analysis ? api.translateText(investigatedReport.churn_analysis, language) : Promise.resolve(''),
          investigatedReport.reader_takeaway ? api.translateText(investigatedReport.reader_takeaway, language) : Promise.resolve('')
        ]);
        if (active) {
          setTranslatedReport({
            headline: tHeadline,
            summary: tSummary,
            accuracy: tAccuracy,
            publisher: tPublisher,
            drifts: tDrifts,
            churn: tChurn,
            takeaway: tTakeaway
          });
        }
      } catch (err) {
        console.warn("Report translation error:", err);
      }
    };
    translateReport();
    return () => { active = false; };
  }, [language, investigatedReport]);

  // Full article translation on read states
  const [selectedLanguage, setSelectedLanguage] = useState<string>(language);
  const [translation, setTranslation] = useState<ArticleTranslationResponse | null>(null);
  const [showOriginal, setShowOriginal] = useState<boolean>(false);
  const [sidebarTranslations, setSidebarTranslations] = useState<Record<string, ArticleTranslationResponse>>({});
  const [translatingSidebarIds, setTranslatingSidebarIds] = useState<Record<string, boolean>>({});

  // Top news auto-translation state
  const [translatedNewsArticles, setTranslatedNewsArticles] = useState<any[]>([]);

  useEffect(() => {
    setSelectedLanguage(language);
  }, [language]);

  useEffect(() => {
    if (language === 'en' || newsArticles.length === 0) {
      setTranslatedNewsArticles([]);
      return;
    }

    let active = true;
    const translateTopNews = async () => {
      try {
        const translated = await Promise.all(
          newsArticles.map(async (art) => {
            const [transTitle, transExcerpt] = await Promise.all([
              api.translateText(art.title, language),
              api.translateText(art.excerpt || art.content || '', language)
            ]);
            return {
              ...art,
              title: transTitle,
              excerpt: transExcerpt,
              content: transExcerpt
            };
          })
        );
        if (active) setTranslatedNewsArticles(translated);
      } catch (err) {
        console.warn("Top news translation failed:", err);
      }
    };

    translateTopNews();
    return () => { active = false; };
  }, [language, newsArticles]);

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
    : (translatedNewsArticles.length > 0 ? translatedNewsArticles : newsArticles);

  const triggerTranslation = async (articleId: string, lang: string, articlesList?: any[]) => {
    if (!articleId) return;
    setSelectedLanguage(lang);
    setLanguage(lang as SupportedLanguage);
    setShowOriginal(false);

    const articles = (articlesList && articlesList.length > 0) ? articlesList : displayArticles;

    // 1. Translate main story
    const mainPromise = (async () => {
      try {
        const data = await api.translateArticle(articleId, lang, false);
        setTranslation(data);
      } catch (err: any) {
        const mainArt = articles[0];
        if (mainArt) {
          const [tTitle, tContent] = await Promise.all([
            api.translateText(mainArt.title, lang),
            api.translateText(mainArt.content || mainArt.excerpt || '', lang)
          ]);
          setTranslation({
            article_id: articleId,
            target_language: lang,
            target_language_name: lang.toUpperCase(),
            translated_title: tTitle,
            translated_content: tContent,
            original_language: 'en',
            original_title: mainArt.title,
            original_content: mainArt.content || mainArt.excerpt,
            cached: false,
            created_at: new Date().toISOString()
          });
        }
      }
    })();

    // 2. Translate all visible sidebar cards in parallel
    const sidebarArticles = articles.slice(1, 8).filter((a: any) => a.id && a.id !== articleId);

    const sidebarPromises = sidebarArticles.map(async (art: any) => {
      setTranslatingSidebarIds(prev => ({ ...prev, [art.id]: true }));
      try {
        const data = await api.translateArticle(art.id, lang, true);
        setSidebarTranslations(prev => ({ ...prev, [art.id]: data }));
      } catch (err) {
        try {
          const [tTitle, tExcerpt] = await Promise.all([
            api.translateText(art.title, lang),
            api.translateText(art.excerpt || '', lang)
          ]);
          setSidebarTranslations(prev => ({
            ...prev,
            [art.id]: {
              article_id: art.id,
              target_language: lang,
              target_language_name: lang.toUpperCase(),
              translated_title: tTitle,
              translated_content: tExcerpt,
              cached: false,
              created_at: new Date().toISOString()
            }
          }));
        } catch (e) {
          console.warn(`Sidebar translation failed for article ${art.id}:`, e);
        }
      } finally {
        setTranslatingSidebarIds(prev => ({ ...prev, [art.id]: false }));
      }
    });

    await Promise.allSettled([mainPromise, ...sidebarPromises]);
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
      <section className="mb-0 w-full">
        <div className="w-full" style={{ display: 'grid', gridTemplateColumns: '14% 72% 14%', padding: '2.5rem 2rem 1rem', alignItems: 'center' }}>

          {/* Left Column */}
          <div style={{ borderRight: '1px solid var(--color-border)', paddingLeft: '1.5rem', paddingRight: '1.5rem', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
            <p className="font-display" style={{ fontStyle: 'italic', fontSize: '1.25rem', marginBottom: '1rem' }}>
              {t.heroQuote}
            </p>
            <span className="font-ui text-sm uppercase font-semibold text-muted">{t.heroAuthor}</span>
          </div>

          {/* Center Column */}
          <div style={{ textAlign: 'center', padding: '0 3rem' }}>
            <h2 className="font-display" style={{ fontSize: 'clamp(2.5rem, 3.5vw, 4.25rem)', margin: '0 auto', lineHeight: 1.08 }}>
              {t.heroHeadline}
            </h2>

            {error && (
              <div className="bg-alert text-white p-4 w-full text-center font-mono mt-4">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>

          {/* Right Column */}
          <div style={{ borderLeft: '1px solid var(--color-border)', paddingLeft: '0.75rem', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
            <p className="font-mono text-muted uppercase" style={{ fontSize: '0.8rem', lineHeight: '1.5', letterSpacing: '0.1em' }}>
              {t.heroSide}
            </p>
          </div>
        </div>

        <div style={{ borderBottom: '1px solid var(--color-ink)', width: '100%' }}></div>
      </section>

      {/* URL Input Section */}
      <section className="mb-8 w-full">
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
            <span className="font-display text-muted" style={{ fontStyle: 'italic', fontSize: '1.1rem' }}>See how the same story<br />changes across sources.</span>
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

            {/* 3-Column Balanced Newspaper Grid */}
            {(() => {
              const mainArticle = displayArticles[0];
              const remainingArticles = displayArticles.slice(1);
              const leftArticles: any[] = [];
              const rightArticles: any[] = [];
              const centerSecondaryArticles: any[] = [];

              remainingArticles.forEach((article, index) => {
                if (index === 0 && remainingArticles.length >= 4) {
                  centerSecondaryArticles.push(article);
                } else if (leftArticles.length <= rightArticles.length) {
                  leftArticles.push(article);
                } else {
                  rightArticles.push(article);
                }
              });

              return (
                <>
                  {/* Left Column */}
                  <div className="newspaper-col-left">
                    {leftArticles.map(article => {
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
                            <div className="font-bold text-ink mb-1">{t.by} {article.source}</div>
                            <div className="text-muted leading-relaxed">{activeExcerpt}</div>
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
                    {mainArticle && (() => {
                      const isCurrentTranslation = Boolean(translation && translation.article_id === mainArticle.id);
                      const activeTitle = (isCurrentTranslation && !showOriginal)
                        ? (translation?.translated_title || mainArticle.title)
                        : mainArticle.title;
                      const activeContent = (isCurrentTranslation && !showOriginal)
                        ? (translation?.translated_content || mainArticle.content || mainArticle.excerpt)
                        : (mainArticle.content || mainArticle.excerpt);
                      const isTranslatedView = isCurrentTranslation && !showOriginal;

                      return (
                        <div key={mainArticle.id} className="newspaper-article main-story border-0">
                          <h3 className="font-display" style={{ fontSize: '2.5rem', lineHeight: '1.1', marginBottom: '1.25rem', textAlign: 'center' }}>
                            {activeTitle}
                          </h3>
                          {mainArticle.imageUrl && (
                            <img src={mainArticle.imageUrl} alt={activeTitle} className="news-image news-main-image" style={{ filter: 'grayscale(100%) contrast(1.2)' }} />
                          )}
                          <div className="news-meta justify-center mt-4">
                            <span>{isTranslatedView && translation ? translation.target_language.toUpperCase() : mainArticle.category}</span>
                            <span className="date">{mainArticle.date}</span>
                          </div>
                          
                          <div className="font-ui text-base mb-6 mt-4">
                            <div className="font-bold mb-3">{t.by} {mainArticle.source}</div>
                            <div className="leading-relaxed space-y-4" style={{ color: 'var(--color-ink)' }}>
                              {activeContent.split(/\n\s*\n/).filter(Boolean).map((para: string, pIdx: number) => (
                                <p key={pIdx} className="mb-3 text-justify">{para.trim()}</p>
                              ))}
                            </div>
                          </div>

                          <div className="flex justify-center mt-6">
                            <a href={mainArticle.link} target="_blank" rel="noopener noreferrer" className="trace-link text-blue font-bold font-mono border border-blue px-6 py-2" style={{ border: '2px solid var(--color-blue)' }}>{t.readMainSource}</a>
                          </div>
                        </div>
                      );
                    })()}
                    
                    {centerSecondaryArticles.length > 0 && (
                      <>
                        <hr style={{ borderTop: '2px solid var(--color-ink)', margin: '2rem 0 1.5rem', opacity: 0.2 }} />
                        
                        {centerSecondaryArticles.map(article => {
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
                                    <Loader2 size={10} className="animate-spin" /> {t.translatingCard}
                                  </span>
                                )}
                              </div>
                              <h3 className="font-display" style={{ fontSize: '1.75rem', lineHeight: '1.1', marginBottom: '1rem', textAlign: 'center' }}>{activeTitle}</h3>
                              <div className="font-ui text-md mb-4 text-center">
                                <div className="font-bold text-ink mb-1">{t.by} {article.source}</div>
                                <div className="text-muted leading-relaxed">{activeExcerpt}</div>
                              </div>
                            </div>
                          );
                        })}
                      </>
                    )}
                  </div>

                  {/* Right Column */}
                  <div className="newspaper-col-right">
                    {rightArticles.map(article => {
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
                            <div className="font-bold text-ink mb-1">{t.by} {article.source}</div>
                            <div className="text-muted leading-relaxed">{activeExcerpt}</div>
                          </div>
                          <a href={article.link} target="_blank" rel="noopener noreferrer" className="trace-link text-blue text-xs font-bold font-mono inline-flex items-center gap-1">
                            {t.readArticle} <ExternalLink size={12}/>
                          </a>
                        </div>
                      );
                    })}
                  </div>
                </>
              );
            })()}

          </div>
        )}
      </section>

      {/* Groq AI Detailed Analysis Section (Rendered when URL search is performed) */}
      {isInvestigating && (
        <div className="px-8 w-full">
          <StoryVerificationReport
            reportData={investigatedReport}
            loadingReport={loadingReport}
            translatedReport={translatedReport}
          />
        </div>
      )}

    </div>
  );
}


