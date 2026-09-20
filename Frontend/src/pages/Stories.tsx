import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { newsArticles } from '../data';
import { useLanguage } from '../context/LanguageContext';

const NewspaperSkeleton = () => (
  <div className="newspaper-layout" style={{ padding: '2rem' }}>
    {/* Left Column Skeleton */}
    <div className="newspaper-col-left">
      <div className="font-mono text-xs font-bold uppercase tracking-widest text-ink mb-6" style={{ borderBottom: '1px solid var(--color-ink)', paddingBottom: '0.5rem' }}>
        DEVELOPING
      </div>
      {[1, 2, 3].map(i => (
        <div key={i} className="newspaper-article">
          <div className="news-meta mb-2">
            <div className="animate-pulse h-3 w-16" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
            <div className="animate-pulse h-3 w-20" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          </div>
          <div className="animate-pulse h-6 w-full mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-6 w-3/4 mb-3" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-1/3 mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-full mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-5/6 mb-3" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-24" style={{ backgroundColor: 'var(--color-blue)', opacity: 0.3 }} />
        </div>
      ))}
    </div>

    {/* Center Column Skeleton */}
    <div className="newspaper-col-center">
      <div style={{ textAlign: 'center', width: '100%', marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div className="animate-pulse h-9 w-64 mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        <div className="animate-pulse h-3 w-48" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        <div aria-hidden="true" style={{ borderBottom: '1px solid #D8D5CC', width: '100%', marginTop: '0.75rem' }} />
      </div>

      {/* Main Headline Skeleton */}
      <div className="newspaper-article border-0 pb-4">
        <div className="news-meta justify-center mb-3">
          <div className="animate-pulse h-3 w-16" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-24" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        </div>
        <div className="animate-pulse h-8 w-5/6 mx-auto mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        <div className="animate-pulse h-8 w-2/3 mx-auto mb-4" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        <div className="animate-pulse h-4 w-32 mx-auto mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        <div className="animate-pulse h-4 w-full mx-auto mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        <div className="animate-pulse h-4 w-5/6 mx-auto mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        <div className="animate-pulse h-4 w-3/4 mx-auto mb-4" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        <div className="flex justify-center mb-4">
          <div className="animate-pulse h-4 w-28" style={{ backgroundColor: 'var(--color-blue)', opacity: 0.3 }} />
        </div>
      </div>

      <div aria-hidden="true" style={{ borderBottom: '1px solid #D8D5CC', width: '100%', margin: '1rem 0 1.5rem' }} />

      {/* Secondary Story Skeletons in Center */}
      {[1, 2, 3].map(i => (
        <div key={i} className="newspaper-article border-b border-border pb-4 mb-4">
          <div className="news-meta justify-center mb-2">
            <div className="animate-pulse h-3 w-14" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
            <div className="animate-pulse h-3 w-20" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          </div>
          <div className="animate-pulse h-6 w-4/5 mx-auto mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-28 mx-auto mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-full mx-auto mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-5/6 mx-auto mb-3" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="flex justify-center">
            <div className="animate-pulse h-3 w-24" style={{ backgroundColor: 'var(--color-blue)', opacity: 0.3 }} />
          </div>
        </div>
      ))}
    </div>

    {/* Right Column Skeleton */}
    <div className="newspaper-col-right">
      <div className="font-mono text-xs font-bold uppercase tracking-widest text-ink mb-6" style={{ borderBottom: '1px solid var(--color-ink)', paddingBottom: '0.5rem' }}>
        MORE STORIES
      </div>
      {[1, 2, 3].map(i => (
        <div key={i} className="newspaper-article">
          <div className="news-meta mb-2">
            <div className="animate-pulse h-3 w-16" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
            <div className="animate-pulse h-3 w-20" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          </div>
          <div className="animate-pulse h-6 w-full mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-6 w-3/4 mb-3" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-1/3 mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-full mb-1" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-5/6 mb-3" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="animate-pulse h-3 w-24" style={{ backgroundColor: 'var(--color-blue)', opacity: 0.3 }} />
        </div>
      ))}
    </div>
  </div>
);

export default function Stories() {
  const { t, language } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [liveNews, setLiveNews] = useState<any[]>(newsArticles);
  const [loadingCategoryNews, setLoadingCategoryNews] = useState(false);

  // Dynamic translated news map
  const [translatedNewsMap, setTranslatedNewsMap] = useState<Record<string, { title: string; excerpt: string }>>({});

  const fetchCategoryNews = async (cat: string) => {
    setLoadingCategoryNews(true);
    try {
      const news = await api.getTopNews(cat);
      if (news && news.length > 0) {
        setLiveNews(news);
      }
    } catch (err) {
      console.warn(`Failed to fetch news for category ${cat}:`, err);
    } finally {
      setLoadingCategoryNews(false);
    }
  };

  const handleCategorySelect = (category: string) => {
    setActiveFilter(category);
    fetchCategoryNews(category);
  };

  useEffect(() => {
    fetchCategoryNews('ALL').finally(() => setLoading(false));
  }, []);

  // Translate live news whenever active language changes
  useEffect(() => {
    if (language === 'en') {
      setTranslatedNewsMap({});
      return;
    }

    let active = true;

    liveNews.forEach(async (art) => {
      try {
        const [transTitle, transExcerpt] = await Promise.all([
          api.translateText(art.title, language),
          api.translateText(art.excerpt || '', language)
        ]);
        if (active) {
          setTranslatedNewsMap(prev => ({ ...prev, [art.id]: { title: transTitle, excerpt: transExcerpt } }));
        }
      } catch (e) {
        console.warn("News translation failed:", e);
      }
    });

    return () => { active = false; };
  }, [language, liveNews]);

  return (
    <div className="flex flex-col w-full">
      {/* Latest News Section */}
      <section className="mb-12 w-full">
        {/* Category navigation */}
        <div style={{ borderBottom: '1px solid var(--color-ink)', padding: '0.65rem 2rem', display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', background: 'transparent' }}>
          <div className="filters font-mono flex items-center justify-center flex-wrap gap-2 text-xs">
            {['ALL', 'WORLD', 'INDIA', 'TECH', 'BUSINESS', 'SCIENCE', 'POLITICS', 'ENVIRONMENT', 'SPORTS'].map((category, index, categories) => (
              <span key={category} className="flex items-center gap-2">
                <span
                  onClick={() => handleCategorySelect(category)}
                  className={`cursor-pointer transition-colors uppercase font-bold ${activeFilter === category ? 'filter-active text-blue underline' : 'hover:text-blue'}`}
                >
                  {category}
                </span>
                {index < categories.length - 1 && <span className="text-muted" style={{ opacity: 0.4, userSelect: 'none' }}>|</span>}
              </span>
            ))}
          </div>
        </div>

        {loadingCategoryNews || loading ? (
          <NewspaperSkeleton />
        ) : (() => {
          const visibleNews = liveNews;
          const centerMain = visibleNews.length ? visibleNews[0] : null;
          const centerSub = visibleNews.slice(1, 4);
          const left = visibleNews.slice(4, 7);
          const right = visibleNews.slice(7);

          return (
            <div className="newspaper-layout" style={{ padding: '2rem' }}>
              {/* Left Column (3 Articles) */}
              <div className="newspaper-col-left">
                <div className="font-mono text-xs font-bold uppercase tracking-widest text-ink mb-6" style={{ borderBottom: '1px solid var(--color-ink)', paddingBottom: '0.5rem' }}>
                  DEVELOPING
                </div>
                {left.map((article, idx) => {
                  const trans = translatedNewsMap[article.id];
                  const activeTitle = trans?.title || article.title;
                  const activeExcerpt = trans?.excerpt || article.excerpt;

                  return (
                    <Link to={article.link} key={article.id} className={`newspaper-article block group hover:opacity-90 transition-opacity ${idx === left.length - 1 ? 'border-0 pb-0' : ''}`}>
                      <div className="news-meta mb-2">
                        <span>{article.category}</span>
                        <span className="text-muted">·</span>
                        <span className="date">{article.date.split(',')[0]}</span>
                      </div>
                      <h3 className="font-display mb-2" style={{ fontSize: '1.4rem', lineHeight: '0.95' }}>{activeTitle}</h3>
                      <div className="font-ui text-sm mb-2">
                        <div className="font-bold mb-1 text-ink">{t.by} {article.source}</div>
                        <div className="text-muted leading-snug">{activeExcerpt}</div>
                      </div>
                      <div className="mt-2 font-mono text-xs font-bold text-blue opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                        FULL ARTICLE &rarr;
                      </div>
                    </Link>
                  );
                })}
              </div>

              {/* Center Column (1 Main Story + 3 Secondary Stories) */}
              <div className="newspaper-col-center">
                {/* Centered LATEST NEWS Headline */}
                <div style={{ textAlign: 'center', width: '100%', marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <h1 className="font-display text-center" style={{ margin: 0, fontSize: '2.5rem', lineHeight: 1, letterSpacing: '0.04em', textTransform: 'uppercase', textAlign: 'center', width: '100%' }}>
                    {activeFilter === 'ALL' ? 'LATEST NEWS' : `${activeFilter} STORIES`}
                  </h1>
                  <span className="font-mono text-muted uppercase text-center" style={{ fontSize: '0.65rem', letterSpacing: '0.15em', marginTop: '0.35rem', textAlign: 'center', display: 'block', width: '100%' }}>
                    REAL STORIES. MULTIPLE PERSPECTIVES.
                  </span>
                  <div aria-hidden="true" style={{ borderBottom: '1px solid #D8D5CC', width: '100%', marginTop: '0.75rem' }} />
                </div>

                {/* Main Headline Story */}
                {centerMain && (() => {
                  const trans = translatedNewsMap[centerMain.id];
                  const activeTitle = trans?.title || centerMain.title;
                  const activeExcerpt = trans?.excerpt || centerMain.excerpt;

                  return (
                    <div className="newspaper-article main-story border-0 pb-0 mb-6">
                      <div className="news-meta justify-center mb-3">
                        <span>{centerMain.category}</span>
                        <span className="text-muted">·</span>
                        <span className="date">{centerMain.date}</span>
                      </div>
                      <h3 className="font-display uppercase" style={{ fontSize: '2.1rem', lineHeight: '0.92', marginBottom: '1.25rem', textAlign: 'center' }}>
                        {activeTitle}
                      </h3>
                      <div className="font-ui text-md mb-[16px] text-center mx-auto" style={{ maxWidth: '700px' }}>
                        <div className="font-bold mb-2 uppercase tracking-wide text-xs">{t.by} {centerMain.source}</div>
                        <div className="excerpt mt-1 text-ink leading-relaxed">{activeExcerpt}</div>
                      </div>
                      <div className="flex justify-center mb-4 group">
                        <Link to={centerMain.link} className="font-bold font-mono text-blue transition-transform hover:translate-x-1 relative inline-block text-xs tracking-wider uppercase">
                          FULL ARTICLE &rarr;
                          <span className="absolute left-0 bottom-[-2px] w-full h-[1px] bg-blue scale-x-0 group-hover:scale-x-100 transition-transform origin-left"></span>
                        </Link>
                      </div>
                    </div>
                  );
                })()}

                {centerSub.length > 0 && (
                  <div aria-hidden="true" style={{ borderBottom: '1px solid #D8D5CC', width: '100%', margin: '1rem 0 1.5rem' }} />
                )}

                {/* 3 Secondary Stories in Center Column */}
                {centerSub.map((article, idx) => {
                  const trans = translatedNewsMap[article.id];
                  const activeTitle = trans?.title || article.title;
                  const activeExcerpt = trans?.excerpt || article.excerpt;

                  return (
                    <Link to={article.link} key={article.id} className={`newspaper-article block group hover:opacity-90 transition-opacity ${idx === centerSub.length - 1 ? 'border-0 pb-0' : 'mb-4 pb-4 border-b border-border'}`}>
                      <div className="news-meta justify-center mb-2">
                        <span>{article.category}</span>
                        <span className="text-muted">·</span>
                        <span className="date">{article.date.split(',')[0]}</span>
                      </div>
                      <h3 className="font-display" style={{ fontSize: '1.5rem', lineHeight: '0.95', marginBottom: '0.75rem', textAlign: 'center' }}>
                        {activeTitle}
                      </h3>
                      <div className="font-ui text-sm mb-3 text-center">
                        <div className="font-bold mb-1 text-ink">{t.by} {article.source}</div>
                        <div className="text-muted leading-snug">{activeExcerpt}</div>
                      </div>
                      <div className="font-mono text-xs font-bold text-blue opacity-0 group-hover:opacity-100 transition-opacity flex justify-center items-center gap-1">
                        FULL ARTICLE &rarr;
                      </div>
                    </Link>
                  );
                })}
              </div>

              {/* Right Column (3 Articles) */}
              <div className="newspaper-col-right">
                <div className="font-mono text-xs font-bold uppercase tracking-widest text-ink mb-6" style={{ borderBottom: '1px solid var(--color-ink)', paddingBottom: '0.5rem' }}>
                  MORE STORIES
                </div>
                {right.map((article, idx) => {
                  const trans = translatedNewsMap[article.id];
                  const activeTitle = trans?.title || article.title;
                  const activeExcerpt = trans?.excerpt || article.excerpt;

                  return (
                    <Link to={article.link} key={article.id} className={`newspaper-article block group hover:opacity-90 transition-opacity ${idx === right.length - 1 ? 'border-0 pb-0' : ''}`}>
                      <div className="news-meta mb-2">
                        <span>{article.category}</span>
                        <span className="text-muted">·</span>
                        <span className="date">{article.date.split(',')[0]}</span>
                      </div>
                      <h3 className="font-display mb-2" style={{ fontSize: '1.4rem', lineHeight: '0.95' }}>{activeTitle}</h3>
                      <div className="font-ui text-sm mb-2">
                        <div className="font-bold mb-1 text-ink">{t.by} {article.source}</div>
                        <div className="text-muted leading-snug">{activeExcerpt}</div>
                      </div>
                      <div className="mt-2 font-mono text-xs font-bold text-blue opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                        FULL ARTICLE &rarr;
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })()}
      </section>
    </div>
  );
}
