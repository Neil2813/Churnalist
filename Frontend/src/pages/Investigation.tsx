import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Globe, ArrowLeft, 
  ExternalLink 
} from 'lucide-react';
import { api } from '../api';
import type { EventDetailResponse, DriftReport, Correction, ReportResponse, ArticleTranslationResponse } from '../api';

import { useLanguage } from '../context/LanguageContext';
import { StoryVerificationReport } from '../components/StoryVerificationReport';

export default function Investigation() {
  const { language } = useLanguage();
  const { eventId } = useParams<{ eventId: string }>();
  const [eventData, setEventData] = useState<EventDetailResponse | null>(null);
  const [driftData, setDriftData] = useState<DriftReport | null>(null);
  const [corrections, setCorrections] = useState<Correction[]>([]);
  const [reportData, setReportData] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Full article translation states
  const [articleTranslations, setArticleTranslations] = useState<Record<string, ArticleTranslationResponse>>({});
  const [translatingArticles, setTranslatingArticles] = useState<Record<string, boolean>>({});
  const [showOriginalMap, setShowOriginalMap] = useState<Record<string, boolean>>({});
  const [expandedReaderMap, setExpandedReaderMap] = useState<Record<string, boolean>>({});

  const handleTranslateArticle = async (articleId: string, targetLang?: string) => {
    const lang = targetLang || language || 'en';
    setTranslatingArticles(prev => ({ ...prev, [articleId]: true }));
    try {
      const trans = await api.translateArticle(articleId, lang);
      setArticleTranslations(prev => ({ ...prev, [articleId]: trans }));
      setExpandedReaderMap(prev => ({ ...prev, [articleId]: true }));
      setShowOriginalMap(prev => ({ ...prev, [articleId]: false }));
    } catch (err: any) {
      console.error("Failed to translate article:", err);
    } finally {
      setTranslatingArticles(prev => ({ ...prev, [articleId]: false }));
    }
  };

  // Auto-translate articles when global language changes
  useEffect(() => {
    if (!eventData || !eventData.articles || eventData.articles.length === 0) return;
    eventData.articles.forEach(art => {
      handleTranslateArticle(art.id, language);
    });
  }, [language, eventData?.id]);

  // Use ref to track active polling and prevent duplicates in strict mode
  const isPolling = useRef(false);

  useEffect(() => {
    if (!eventId) return;
    
    let active = true;
    
    const pollEvent = async () => {
      if (!active) return;
      try {
        const evDetail = await api.getEvent(eventId);
        if (active) setEventData(evDetail);
        
        if (evDetail.status === 'READY' || evDetail.article_count > 0) {
          fetchAnalysis(eventId);
          if (evDetail.status !== 'READY') {
            setTimeout(pollEvent, 5000);
          } else {
             setLoading(false);
          }
        } else {
          setTimeout(pollEvent, 3000);
        }
      } catch (err: any) {
        if (active) {
          setError(err.message || 'Failed to poll event details.');
          setLoading(false);
        }
      }
    };

    const fetchAnalysis = async (id: string) => {
      try {
        if (active) setLoadingReport(true);
        const [drift, corr, rpt] = await Promise.all([
          api.getClaimsDrift(id).catch(() => null),
          api.getCorrections(id).catch(() => []),
          api.triggerAnalysis(id).catch(() => api.getReport(id).catch(() => null))
        ]);
        if (active) {
          if (drift) setDriftData(drift);
          if (corr) setCorrections(corr);
          if (rpt) setReportData(rpt);
        }
      } catch (err) {
        console.error("Analysis not ready or failed:", err);
      } finally {
        if (active) {
          setLoading(false);
          setLoadingReport(false);
        }
      }
    };

    if (!isPolling.current) {
      isPolling.current = true;
      pollEvent();
    }

    return () => {
      active = false;
      isPolling.current = false;
    };
  }, [eventId]);

  if (error) {
    return (
      <div className="bg-alert text-white p-4">
        <strong>Error:</strong> {error}
        <Link to="/" className="block mt-4 underline">Return Home</Link>
      </div>
    );
  }

  if (!eventData && loading) {
    return (
      <div className="fade-in mt-4 pb-16 animate-pulse">
        <div className="mb-8">
          <div className="h-6 w-24 mb-3" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="h-8 w-2/3 mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="h-4 w-1/2 mb-4" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <hr className="editorial-rule mt-4" />
        </div>
        <div className="newsroom-grid">
          <div className="flex flex-col gap-4">
            <div className="h-6 w-48 mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
            {[1, 2, 3].map(i => (
              <div key={i} className="border-all p-4 bg-white shadow-sm">
                <div className="h-4 w-28 mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
                <div className="h-6 w-full mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
                <div className="h-3 w-40 mb-3" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
                <div className="h-3 w-24" style={{ backgroundColor: 'var(--color-blue)', opacity: 0.3 }} />
              </div>
            ))}
          </div>
          <div>
            <div className="h-6 w-36 mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
            {[1, 2].map(i => (
              <div key={i} className="evidence-strip bg-white border-all p-4 mb-4">
                <div className="h-5 w-32 mb-3" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
                <div className="grid grid-cols-2 gap-4">
                  <div className="h-12 w-full" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
                  <div className="h-12 w-full" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.1 }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!eventData) return null;

  return (
    <div className="fade-in py-6 container mx-auto">
      {/* Navigation Header */}
      <div className="flex justify-between items-center mb-6 pb-3 border-b border-border">
        <Link to="/stories" className="inline-flex items-center gap-1.5 font-ui font-bold text-xs text-muted hover:text-ink transition-colors uppercase">
          <ArrowLeft size={14} /> BACK TO STORIES
        </Link>
        <Link to={`/provenance/${eventId}`} className="inline-flex items-center gap-1.5 font-ui font-bold text-xs text-blue hover:underline uppercase">
          VIEW PROVENANCE GRAPH <Globe size={14} />
        </Link>
      </div>

      {/* Main Investigation Table Forensics Interface */}
      <StoryVerificationReport
        eventData={eventData}
        driftData={driftData}
        corrections={corrections}
        reportData={reportData}
        loadingReport={loadingReport}
      />

      {/* Ingested Source Articles Reference Table */}
      {eventData.articles && eventData.articles.length > 0 && (
        <div className="mt-10 pt-6 border-t-2 border-ink">
          <div className="section-title-editorial mb-3">
            <span>INGESTED SOURCE ARTICLES</span>
            <span className="font-mono text-xs font-bold text-muted uppercase">
              {eventData.articles.length} SOURCES INDEXED
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="editorial-table">
              <thead>
                <tr>
                  <th style={{ width: '22%' }}>SOURCE</th>
                  <th style={{ width: '12%' }}>LANGUAGE</th>
                  <th style={{ width: '42%' }}>ARTICLE HEADLINE</th>
                  <th style={{ width: '14%' }}>PUBLISHED</th>
                  <th style={{ width: '10%' }}>CONTROLS</th>
                </tr>
              </thead>
              <tbody>
                {eventData.articles.map((art) => {
                  const trans = articleTranslations[art.id];
                  const isTranslating = Boolean(translatingArticles[art.id]);
                  const showOriginal = Boolean(showOriginalMap[art.id]);
                  const isExpanded = Boolean(expandedReaderMap[art.id]);
                  const targetLang = language || 'en';

                  const activeTitle = (trans && !showOriginal) ? (trans.translated_title || art.title) : art.title;
                  const activeContent = (trans && !showOriginal) ? trans.translated_content : (trans ? (trans.original_content || art.content) : art.content);

                  return (
                    <React.Fragment key={art.id}>
                      <tr className="hover:bg-paper-dark">
                        <td className="font-semibold">{art.source_name || "News Outlet"}</td>
                        <td>
                          <span className="badge-status badge-indexed uppercase">
                            {trans && !showOriginal ? `${trans.original_language?.toUpperCase()} → ${trans.target_language.toUpperCase()}` : (art.language || "EN")}
                          </span>
                        </td>
                        <td className="font-display font-semibold text-sm">{activeTitle}</td>
                        <td className="font-mono text-xs text-muted">
                          {art.published_at ? new Date(art.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '11:00 AM'}
                        </td>
                        <td>
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => handleTranslateArticle(art.id, targetLang)}
                              disabled={isTranslating}
                              className="font-mono text-[10px] px-2 py-0.5 uppercase font-bold text-blue border border-blue bg-white hover:bg-blue hover:text-white transition-colors"
                            >
                              {isTranslating ? '...' : (trans ? 'Translated' : 'Translate')}
                            </button>

                            <button
                              type="button"
                              onClick={() => setExpandedReaderMap(prev => ({ ...prev, [art.id]: !prev[art.id] }))}
                              className="font-mono text-[10px] px-2 py-0.5 uppercase font-bold text-ink border border-ink bg-paper hover:bg-ink hover:text-paper transition-colors"
                            >
                              {isExpanded ? 'Close' : 'Read'}
                            </button>
                          </div>
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr className="bg-paper-dark">
                          <td colSpan={5} className="p-4 border-b border-border">
                            <div className="flex justify-between items-center mb-2 font-mono text-xs text-muted border-b border-border pb-1">
                              <span>
                                {!showOriginal && trans ? (
                                  <>Translated into <strong className="text-blue uppercase">{trans.target_language_name}</strong></>
                                ) : (
                                  <>Original content ({art.language || "EN"})</>
                                )}
                              </span>
                              <a href={art.url} target="_blank" rel="noreferrer" className="text-blue font-bold hover:underline inline-flex items-center gap-1">
                                <Globe size={11} /> ORIGINAL SOURCE <ExternalLink size={10} />
                              </a>
                            </div>
                            <div className="font-ui text-xs text-ink leading-relaxed space-y-2 max-h-60 overflow-y-auto pr-1">
                              {activeContent ? (
                                activeContent.split(/\n\s*\n/).filter(Boolean).map((p: string, pIdx: number) => (
                                  <p key={pIdx} className="m-0">{p.trim()}</p>
                                ))
                              ) : (
                                <p className="italic text-muted m-0">Article body text not available.</p>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

