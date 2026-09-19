import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Loader2, Calendar, ArrowRight } from 'lucide-react';
import { api } from '../api';
import type { EventResponse } from '../api';
import { format } from 'date-fns';
import { newsArticles } from '../data';

export default function Stories() {
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [liveNews, setLiveNews] = useState<any[]>(newsArticles);
  const [featuredIndex, setFeaturedIndex] = useState(0);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const data = await api.listEvents();
        setEvents(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load stories.');
      } finally {
        setLoading(false);
      }
    };
    
    const fetchNews = async () => {
      try {
        const news = await api.getTopNews();
        if (news && news.length > 0) {
          const normalizedNews = news.map((article: any) => ({
            ...article,
            category: article.category === 'ECONOMY' ? 'BUSINESS' : article.category,
          }));
          // The live source may not contain every desk on a given refresh.
          // Retain a story for any missing desk so both side feeds stay complete.
          const liveCategories = new Set(normalizedNews.map((article: any) => article.category));
          const deskFallbacks = newsArticles.filter((article) => !liveCategories.has(article.category));
          setLiveNews([...normalizedNews, ...deskFallbacks]);
        }
      } catch (err) {
        console.warn("Failed to fetch live news, falling back to hardcoded data", err);
      }
    };

    fetchEvents();
    fetchNews();
  }, []);

  // Keep the central lead story fresh, like a news gallery, while preserving
  // the feed order returned by the API (newest item first).
  useEffect(() => {
    setFeaturedIndex(0);
    if (liveNews.length < 2) return;

    const rotation = window.setInterval(() => {
      setFeaturedIndex((current) => (current + 1) % liveNews.length);
    }, 7000);

    return () => window.clearInterval(rotation);
  }, [liveNews]);

  return (
    <div className="flex flex-col w-full">
      {/* Latest News Section */}
      <section className="mb-12 w-full">
        {/* Category navigation */}
        <div style={{ borderBottom: '1px solid var(--color-ink)', padding: '0.65rem 2rem', display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', background: 'transparent' }}>
          <div className="filters font-mono flex items-center justify-center flex-wrap gap-2 text-xs">
            {['ALL', 'WORLD', 'INDIA', 'TECH', 'BUSINESS', 'SCIENCE', 'POLITICS', 'ENVIRONMENT'].map((category, index, categories) => (
              <span key={category} className="flex items-center gap-2">
                <span
                  onClick={() => {
                    setActiveFilter(category);
                    setFeaturedIndex(0);
                  }}
                  className={`cursor-pointer transition-colors ${activeFilter === category ? 'filter-active' : 'hover:text-blue'}`}
                >
                  {category}
                </span>
                {index < categories.length - 1 && <span className="text-muted" style={{ opacity: 0.4, userSelect: 'none' }}>|</span>}
              </span>
            ))}
          </div>
        </div>
        {(() => {
          const leftCategories = ['WORLD', 'INDIA', 'TECH', 'BUSINESS'];
          const rightCategories = ['SCIENCE', 'POLITICS', 'ENVIRONMENT'];
          const isAllStories = activeFilter === 'ALL';
          const visibleNews = isAllStories
            ? liveNews
            : liveNews.filter((article) => article.category === activeFilter);
          const featured = visibleNews.length ? visibleNews[featuredIndex % visibleNews.length] : null;
          const storiesForDesks = (categories: string[]) => categories.flatMap((category) =>
            liveNews.filter((article) => article.category === category).slice(0, 1)
          );
          // All shows the curated desk layout. A selected category shows only
          // stories from that category, distributed across the same columns.
          const center = isAllStories
            ? (featured ? [featured] : [])
            : visibleNews.slice(0, 1);
          const left = isAllStories
            ? storiesForDesks(leftCategories)
            : visibleNews.slice(1, 4);
          const right = isAllStories
            ? storiesForDesks(rightCategories)
            : visibleNews.slice(4);

          return (
            <div className="newspaper-layout" style={{ padding: '2rem' }}>
              <div className="newspaper-col-left">
                <div className="font-mono text-xs font-bold uppercase tracking-widest text-ink mb-6" style={{ borderBottom: '1px solid var(--color-ink)', paddingBottom: '0.5rem' }}>
                  DEVELOPING
                </div>
                {left.map((article, idx) => (
                  <Link to={article.link} key={article.id} className={`newspaper-article block group hover:opacity-90 transition-opacity ${idx === left.length - 1 ? 'border-0 pb-0' : ''}`}>
                    <div className="news-meta mb-2">
                      <span>{article.category}</span>
                      <span className="text-muted">·</span>
                      <span className="date">{article.date.split(',')[0]}</span>
                    </div>
                    <h3 className="font-display mb-2" style={{ fontSize: idx === 2 ? '1.25rem' : '1.5rem', lineHeight: '0.95' }}>{article.title}</h3>
                    {idx < 2 && (
                      <div className="font-ui text-sm mb-2">
                        <div className="font-bold mb-1 text-ink">{article.source}</div>
                        {idx === 0 && <div className="text-muted leading-snug">{article.excerpt}</div>}
                        {idx === 1 && <div className="text-muted leading-snug line-clamp-1">{article.excerpt}</div>}
                      </div>
                    )}
                    <div className="mt-2 font-mono text-xs font-bold text-blue opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                      SEE CHANGES &rarr;
                    </div>
                  </Link>
                ))}
              </div>
              <div className="newspaper-col-center">
                {/* Centered LATEST NEWS Headline */}
                <div style={{ textAlign: 'center', width: '100%', marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <h1 className="font-display text-center" style={{ margin: 0, fontSize: '2.5rem', lineHeight: 1, letterSpacing: '0.04em', textTransform: 'uppercase', textAlign: 'center', width: '100%' }}>
                    LATEST NEWS
                  </h1>
                  <span className="font-mono text-muted uppercase text-center" style={{ fontSize: '0.65rem', letterSpacing: '0.15em', marginTop: '0.35rem', textAlign: 'center', display: 'block', width: '100%' }}>
                    REAL STORIES. MULTIPLE PERSPECTIVES.
                  </span>
                  <div aria-hidden="true" style={{ borderBottom: '1px solid #D8D5CC', width: '100%', marginTop: '0.75rem' }} />
                </div>

                {center.map((article, i) => (
                  <div key={article.id} className="newspaper-article main-story border-0 pb-0">
                    {i === 0 ? (
                      <>
                        <div className="news-meta justify-center mb-4">
                          <span>{isAllStories ? 'ALL' : activeFilter}</span>
                          <span className="text-muted">·</span>
                          <span className="date">{article.date}</span>
                        </div>
                        <h3 className="font-display uppercase" style={{ fontSize: '2.2rem', lineHeight: '0.92', marginBottom: '1.5rem', textAlign: 'center' }}>
                          {article.title}
                        </h3>
                        {article.imageUrl && (
                          <div className="mb-6">
                            <img src={article.imageUrl} alt={article.title} className="news-image news-main-image w-full object-cover mb-[24px]" style={{ filter: 'grayscale(100%) contrast(1.2)' }} />
                            <div className="text-center font-ui text-[0.65rem] text-muted uppercase tracking-wider mb-[10px]">
                              News coverage of escalating airstrikes and their international response.<br/>
                              {article.source}, {article.date.split(',')[0]}
                            </div>
                          </div>
                        )}
                        <div className="font-ui text-lg mb-[20px] text-center mx-auto" style={{ maxWidth: '700px' }}>
                          <div className="font-bold mb-2 uppercase tracking-wide text-sm">{article.source}</div>
                          <div className="excerpt mt-2 text-ink leading-relaxed">{article.excerpt}</div>
                        </div>
                        <div className="flex justify-center mb-8 group">
                          <Link to={article.link} className="font-bold font-mono text-blue transition-transform hover:translate-x-1 relative inline-block text-sm tracking-wider uppercase">
                            SEE WHAT CHANGED &rarr;
                            <span className="absolute left-0 bottom-[-2px] w-full h-[1px] bg-blue scale-x-0 group-hover:scale-x-100 transition-transform origin-left"></span>
                          </Link>
                        </div>
                      </>
                    ) : (
                      <Link to={article.link} className="block group hover:opacity-90 transition-opacity">
                        <div className="news-meta justify-center mt-4 mb-2">
                          <span>{article.category}</span>
                          <span className="text-muted">·</span>
                          <span className="date">{article.date.split(',')[0]}</span>
                        </div>
                        <h3 className="font-display" style={{ fontSize: '1.75rem', lineHeight: '0.95', marginBottom: '1rem', textAlign: 'center' }}>
                          {article.title}
                        </h3>
                        <div className="font-ui text-md mb-4 text-center">
                          <div className="font-bold mb-1 text-ink">{article.source}</div>
                          <div style={{ color: 'var(--color-ink)' }}>{article.excerpt}</div>
                        </div>
                        <div className="font-mono text-xs font-bold text-blue opacity-0 group-hover:opacity-100 transition-opacity flex justify-center items-center gap-1">
                          SEE CHANGES &rarr;
                        </div>
                      </Link>
                    )}
                    {/* hr removed per request */}
                  </div>
                ))}
              </div>
              <div className="newspaper-col-right">
                <div className="font-mono text-xs font-bold uppercase tracking-widest text-ink mb-6" style={{ borderBottom: '1px solid var(--color-ink)', paddingBottom: '0.5rem' }}>
                  MORE STORIES
                </div>
                {right.map((article, idx) => (
                  <Link to={article.link} key={article.id} className={`newspaper-article block group hover:opacity-90 transition-opacity ${idx === right.length - 1 ? 'border-0 pb-0' : ''}`}>
                    <div className="news-meta mb-2">
                      <span>{article.category}</span>
                      <span className="text-muted">·</span>
                      <span className="date">{article.date.split(',')[0]}</span>
                    </div>
                    <h3 className="font-display mb-2" style={{ fontSize: idx === 2 ? '1.25rem' : '1.5rem', lineHeight: '0.95' }}>{article.title}</h3>
                    {idx < 2 && (
                      <div className="font-ui text-sm mb-2">
                        <div className="font-bold mb-1 text-ink">{article.source}</div>
                        {idx === 0 && <div className="text-muted leading-snug">{article.excerpt}</div>}
                        {idx === 1 && <div className="text-muted leading-snug line-clamp-1">{article.excerpt}</div>}
                      </div>
                    )}
                    <div className="mt-2 font-mono text-xs font-bold text-blue opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                      SEE CHANGES &rarr;
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          );
        })()}
      </section>

      {/* Tracked Events Section */}
      <section className="mb-12 w-full">
        <div style={{ padding: '2.5rem 2rem 1.75rem', textAlign: 'center', borderBottom: '1px solid var(--color-ink)' }}>
          <h2 className="font-display" style={{ margin: 0, fontSize: '3.2rem', lineHeight: 1, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
            TRACKED EVENTS
          </h2>
          <span className="font-mono text-muted uppercase inline-block" style={{ fontSize: '0.75rem', letterSpacing: '0.15em', marginTop: '0.6rem' }}>
            OUR ONGOING INVESTIGATIONS.
          </span>
        </div>
        <div style={{ padding: '2rem' }}>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="animate-spin text-muted" size={32} />
            </div>
          ) : error ? (
            <div className="bg-alert text-white p-4 font-mono">
              <strong>Error:</strong> {error}
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-12 text-muted font-mono uppercase">
              No tracked events found.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {events.map((ev) => (
                <Link to={`/investigate/${ev.id}`} key={ev.id} className="border p-4 hover:border-blue transition-colors flex flex-col h-full bg-paper">
                  <div className="flex justify-between items-start mb-4">
                    <div className="bg-blue text-white font-mono text-xs px-2 py-1 uppercase">{ev.status}</div>
                    <div className="flex items-center text-muted text-xs font-mono">
                      <Calendar size={12} className="mr-1" />
                      {format(new Date((ev as any).created_at || Date.now()), 'dd MMM yyyy').toUpperCase()}
                    </div>
                  </div>
                  
                  <h3 className="font-display text-2xl mb-2 flex-grow">
                    {ev.title || 'Untitled Investigation'}
                  </h3>
                  
                  <div className="text-muted text-sm font-ui line-clamp-3 mb-6">
                    {(ev as any).summary || 'No summary available.'}
                  </div>
                  
                  <div className="border-t pt-4 mt-auto">
                    <div className="flex justify-between items-center text-xs font-mono text-muted">
                      <span className="flex items-center gap-1"><FileText size={12} /> {ev.article_count || (ev as any).articles?.length || 0} SOURCES</span>
                      <span className="flex items-center gap-1 hover:text-blue text-ink font-bold">VIEW REPORT <ArrowRight size={12} /></span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
