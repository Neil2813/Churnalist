import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Loader2, FileText, Globe, AlertTriangle, ArrowLeft, 
  Sparkles, Cpu, CheckCircle2, Clock, GitCompare, Flame, 
  ShieldCheck, ExternalLink, Languages 
} from 'lucide-react';
import { api } from '../api';
import type { EventDetailResponse, DriftReport, Correction, ReportResponse, ArticleTranslationResponse } from '../api';

const SUPPORTED_TRANSLATION_LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi (हिन्दी)' },
  { code: 'ta', name: 'Tamil (தமிழ்)' },
  { code: 'te', name: 'Telugu (తెలుగు)' },
  { code: 'bn', name: 'Bengali (বাংলা)' },
  { code: 'kn', name: 'Kannada (ಕನ್ನಡ)' },
];

export default function Investigation() {
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
  const [translationErrors, setTranslationErrors] = useState<Record<string, string | null>>({});
  const [showOriginalMap, setShowOriginalMap] = useState<Record<string, boolean>>({});
  const [targetLangMap, setTargetLangMap] = useState<Record<string, string>>({});
  const [expandedReaderMap, setExpandedReaderMap] = useState<Record<string, boolean>>({});

  const handleTranslateArticle = async (articleId: string, targetLang?: string) => {
    const lang = targetLang || targetLangMap[articleId] || 'en';
    setTranslatingArticles(prev => ({ ...prev, [articleId]: true }));
    setTranslationErrors(prev => ({ ...prev, [articleId]: null }));
    try {
      const trans = await api.translateArticle(articleId, lang);
      setArticleTranslations(prev => ({ ...prev, [articleId]: trans }));
      setExpandedReaderMap(prev => ({ ...prev, [articleId]: true }));
      setShowOriginalMap(prev => ({ ...prev, [articleId]: false }));
    } catch (err: any) {
      console.error("Failed to translate article:", err);
      setTranslationErrors(prev => ({
        ...prev,
        [articleId]: err?.message || 'Translation failed, please try again',
      }));
    } finally {
      setTranslatingArticles(prev => ({ ...prev, [articleId]: false }));
    }
  };

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
      <div className="flex flex-col items-center justify-center p-16 border-all border-dashed mt-8">
        <Loader2 className="animate-spin mb-4" size={32} />
        <h3 className="font-display text-xl mb-2">Investigating Sources...</h3>
        <p className="text-muted font-mono">Querying global news APIs and cross-referencing claims.</p>
      </div>
    );
  }

  if (!eventData) return null;

  return (
    <div className="fade-in mt-4 pb-16">
      {/* Navigation Header */}
      <div className="flex justify-between items-center mb-6">
        <Link to="/stories" className="inline-flex items-center gap-2 font-ui font-semibold text-sm text-muted hover:text-ink transition-colors">
          <ArrowLeft size={16} /> BACK TO STORIES
        </Link>
        <Link to={`/provenance/${eventId}`} className="inline-flex items-center gap-2 font-ui font-semibold text-sm text-blue hover:underline">
          VIEW PROVENANCE GRAPH <Globe size={16} />
        </Link>
      </div>
      
      {/* Event Header */}
      <div className="mb-8">
        <span className="font-mono bg-ink text-white px-2 py-1 text-xs uppercase mr-2 font-bold">
          {eventData.status}
        </span>
        <h2 className="font-display inline align-middle text-2xl md:text-3xl">{eventData.title}</h2>
        <p className="text-muted mt-2 font-mono text-sm">Discovered {eventData.article_count} related articles across global news sources.</p>
        <hr className="editorial-rule mt-4" />
      </div>

      {/* Main Grid: Sources & Claim Transformations */}
      <div className="newsroom-grid">
        {/* Left Column: News Grid (Discovered Articles) */}
        <div>
          <h3 className="font-display border-bottom pb-2 mb-4 flex items-center justify-between">
            <span>NEWS GRID & SOURCES</span>
            <span className="font-mono text-xs font-normal text-muted">{eventData.articles.length} SOURCES</span>
          </h3>
          <div className="flex flex-col gap-4">
            {eventData.articles.map(article => {
              const trans = articleTranslations[article.id];
              const isTranslating = Boolean(translatingArticles[article.id]);
              const showOriginal = Boolean(showOriginalMap[article.id]);
              const isExpanded = Boolean(expandedReaderMap[article.id]);
              const targetLang = targetLangMap[article.id] || 'en';

              const activeTitle = (trans && !showOriginal) ? (trans.translated_title || article.title) : article.title;
              const activeContent = (trans && !showOriginal) ? trans.translated_content : (trans ? (trans.original_content || article.content) : article.content);

              return (
                <div key={article.id} className="border-all p-4 bg-white hover:border-ink transition-colors shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-mono text-xs font-bold text-ink uppercase">{article.source_name || "News Outlet"}</span>
                    <span className="font-mono bg-ink text-paper px-1.5 py-0.5 text-[10px] uppercase font-semibold">
                      {trans && !showOriginal ? `${trans.original_language?.toUpperCase()} → ${trans.target_language.toUpperCase()}` : (article.language || "EN")}
                    </span>
                  </div>
                  <h4 className="font-display text-md mb-2 leading-snug">{activeTitle}</h4>
                  {article.published_at && (
                    <span className="font-mono text-[11px] text-muted block mb-3">
                      Published: {new Date(article.published_at).toLocaleString()}
                    </span>
                  )}

                  {/* Translation & Reading Controls */}
                  <div className="pt-2 border-top mt-3 flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <select
                        value={targetLang}
                        onChange={(e) => {
                          const newLang = e.target.value;
                          setTargetLangMap(prev => ({ ...prev, [article.id]: newLang }));
                          handleTranslateArticle(article.id, newLang);
                        }}
                        disabled={isTranslating}
                        className="font-mono text-xs border border-ink bg-white px-2 py-1 cursor-pointer outline-none font-semibold"
                      >
                        {SUPPORTED_TRANSLATION_LANGUAGES.map(l => (
                          <option key={l.code} value={l.code}>{l.name}</option>
                        ))}
                      </select>

                      <button
                        type="button"
                        onClick={() => handleTranslateArticle(article.id, targetLang)}
                        disabled={isTranslating}
                        className="font-mono text-xs px-2.5 py-1 uppercase font-bold flex items-center gap-1"
                      >
                        {isTranslating ? <Loader2 size={10} className="animate-spin" /> : <Languages size={12} />}
                        {isTranslating ? 'Translating...' : (trans ? 'Translate' : 'Translate Article')}
                      </button>

                      {trans && (
                        <button
                          type="button"
                          onClick={() => setShowOriginalMap(prev => ({ ...prev, [article.id]: !prev[article.id] }))}
                          className="outline font-mono text-xs px-2.5 py-1 uppercase font-bold"
                          style={{ border: '1px solid var(--color-ink)' }}
                        >
                          {showOriginal ? 'Show Translation' : 'View Original'}
                        </button>
                      )}
                    </div>

                    <a href={article.url} target="_blank" rel="noreferrer" className="text-xs font-mono font-bold text-blue hover:underline inline-flex items-center gap-1">
                      <Globe size={12} /> ORIGINAL SOURCE <ExternalLink size={10} />
                    </a>
                  </div>

                  {translationErrors[article.id] && (
                    <div className="mt-2 text-alert font-mono text-xs">
                      <strong>Translation Error:</strong> {translationErrors[article.id]}
                    </div>
                  )}

                  {/* Expanded Translation / Article Reader */}
                  {isExpanded && trans && (
                    <div className="mt-4 pt-3 border-top bg-paper p-3 border-all">
                      <div className="flex items-center justify-between text-xs font-mono text-muted mb-3">
                        <span>
                          {!showOriginal ? (
                            <>
                              Translated from <strong className="text-ink uppercase">{trans.original_language_name || trans.original_language}</strong> into <strong className="text-blue uppercase">{trans.target_language_name}</strong>
                            </>
                          ) : (
                            <>
                              Viewing <strong className="text-ink uppercase">Original ({trans.original_language_name || trans.original_language})</strong> text
                            </>
                          )}
                        </span>
                        {trans.cached && (
                          <span className="bg-ink text-paper px-1.5 py-0.5 text-[9px] font-bold uppercase">
                            From Cache
                          </span>
                        )}
                      </div>

                      <div className="font-ui text-sm space-y-3 max-h-96 overflow-y-auto pr-1">
                        {activeContent ? (
                          activeContent.split(/\n\s*\n/).filter(Boolean).map((p: string, pIdx: number) => (
                            <p key={pIdx} className="mb-2 leading-relaxed text-ink">{p.trim()}</p>
                          ))
                        ) : (
                          <p className="text-muted italic">Full article content not available.</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            {eventData.articles.length === 0 && (
              <p className="text-muted italic text-sm p-4 border-all bg-paper">No articles ingested yet. Still fetching live data...</p>
            )}
          </div>
        </div>

        {/* Right Column: Drift Analysis */}
        <div>
          <h3 className="font-display border-bottom pb-2 mb-4">WHAT CHANGED?</h3>
          
          {loading && (
            <p className="text-muted font-mono flex items-center gap-2 mb-4"><Loader2 className="animate-spin" size={16} /> Analyzing claims drift...</p>
          )}

          {driftData && driftData.edges && driftData.edges.length > 0 ? (
            <div className="flex flex-col gap-6">
              {driftData.edges.map((edge, idx) => {
                const sourceNode = driftData.nodes.find(n => n.id === edge.source);
                const targetNode = driftData.nodes.find(n => n.id === edge.target);
                if (!sourceNode || !targetNode) return null;

                return (
                  <div key={idx} className="evidence-strip bg-white border-all p-4">
                    <div className="bg-ink text-paper px-2 py-1 text-xs font-mono font-bold mb-3 uppercase flex items-center gap-2">
                      <AlertTriangle size={14} className="text-alert" /> 
                      {edge.relation_type.replace(/_/g, ' ')}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="border-right pr-4">
                        <span className="text-xs text-muted font-mono block mb-1">ORIGINAL CLAIM ({sourceNode.language ? sourceNode.language.toUpperCase() : 'EN'})</span>
                        <p className="font-display text-md">
                          "{sourceNode.english_translation || sourceNode.label}"
                        </p>
                        {sourceNode.original_text && sourceNode.original_text !== (sourceNode.english_translation || sourceNode.label) && (
                          <p className="font-ui text-xs text-muted mt-1 italic">
                            Native script: "{sourceNode.original_text}"
                          </p>
                        )}
                      </div>
                      <div>
                        <span className="text-xs text-muted font-mono block mb-1">MODIFIED CLAIM ({targetNode.language ? targetNode.language.toUpperCase() : '?'})</span>
                        <p className="font-display text-md text-alert">
                          "{targetNode.original_text || targetNode.label}"
                        </p>
                        {targetNode.english_translation && targetNode.english_translation !== (targetNode.original_text || targetNode.label) && (
                          <p className="font-ui text-xs text-muted mt-1 italic">
                            English translation: "{targetNode.english_translation}"
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            !loading && (
              <div className="bg-paper border-all p-8 text-center text-muted">
                <FileText size={32} className="mx-auto mb-2 opacity-50" />
                <p>No significant claim drift detected or analysis is still running.</p>
              </div>
            )
          )}

          {/* Corrections Section */}
          {corrections.length > 0 && (
            <div className="mt-10">
              <h3 className="font-display border-bottom pb-2 mb-4 text-corrected">CORRECTIONS FOUND</h3>
              <div className="flex flex-col gap-4">
                {corrections.map(corr => (
                  <div key={corr.id} className="border-all border-corrected bg-white p-4">
                    <span className="font-mono text-[10px] bg-corrected text-white px-2 py-1 uppercase mb-2 inline-block">
                      {corr.correction_type.replace(/_/g, ' ')}
                    </span>
                    <div className="grid grid-cols-2 gap-4 mt-2">
                      <div className="border-right pr-4">
                        <span className="text-xs text-muted font-mono block mb-1">ORIGINAL</span>
                        <p className="font-ui text-sm line-through text-muted">{corr.original_text}</p>
                      </div>
                      <div>
                        <span className="text-xs text-corrected font-mono block mb-1">CORRECTED</span>
                        <p className="font-ui text-sm font-semibold">{corr.corrected_text}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Section: Groq Detailed AI Analysis */}
      <div className="mt-14 pt-8" style={{ borderTop: '3px double var(--color-ink)' }}>
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
          {reportData && (
            <div className="flex items-center gap-2 bg-paper border-all px-3 py-1.5 text-xs font-mono">
              <Cpu size={14} className="text-blue" />
              <span className="font-bold">CONFIDENCE SCORE: {(reportData.confidence_score * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>

        {loadingReport && !reportData ? (
          <div className="p-12 border-all border-dashed text-center font-mono text-muted flex flex-col items-center justify-center gap-3 bg-paper">
            <Loader2 size={24} className="animate-spin text-ink" />
            <span className="font-bold text-ink">GROQ LLM IS REASONING OVER ALL SOURCE ARTICLES...</span>
            <span className="text-xs">Analyzing accuracy, original publisher, claim changes, and churnalism values.</span>
          </div>
        ) : reportData ? (
          <div className="flex flex-col gap-6">
            {/* Overview Headline & Summary */}
            <div className="bg-paper border-all p-6 shadow-sm">
              <span className="font-mono text-xs bg-ink text-paper px-2 py-0.5 uppercase mb-2 inline-block font-bold">EXECUTIVE SUMMARY</span>
              <h4 className="font-display text-xl mb-2">{reportData.headline}</h4>
              <p className="font-ui text-md leading-relaxed text-ink mb-0">{reportData.summary}</p>
            </div>

            {/* 4 Deep Insights Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* 1. Accuracy & Truth Assessment */}
              <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #10b981' }}>
                <div className="flex items-center gap-2 text-emerald-700 font-mono font-bold text-xs uppercase mb-3">
                  <CheckCircle2 size={18} /> ACCURACY & TRUTH ASSESSMENT
                </div>
                <p className="font-ui text-sm text-ink leading-relaxed m-0">
                  {reportData.accuracy_analysis || "Core factual claims maintain strong evidence consistency across primary coverage."}
                </p>
              </div>

              {/* 2. First Publisher / Origin */}
              <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #3b82f6' }}>
                <div className="flex items-center gap-2 text-blue font-mono font-bold text-xs uppercase mb-3">
                  <Clock size={18} /> FIRST PUBLISHER & ORIGIN
                </div>
                <div className="font-ui text-sm">
                  <span className="font-bold text-ink block mb-1">
                    Published First By: <span className="text-blue font-mono">{reportData.first_publisher || "Primary Publisher"}</span>
                  </span>
                  {reportData.first_published_at && (
                    <span className="font-mono text-xs text-muted block">
                      Original Timestamp: {reportData.first_published_at}
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
                  {reportData.key_drifts && reportData.key_drifts.length > 0 
                    ? `${reportData.key_drifts.length} claim modifications identified across editions (e.g., ${reportData.key_drifts[0].explanation}).`
                    : "No significant claim modifications or numerical alterations detected across compared article versions."}
                </p>
              </div>

              {/* 4. Churnalism & Fake / Exaggerated Values */}
              <div className="border-all p-5 bg-white shadow-sm" style={{ borderLeft: '5px solid #ef4444' }}>
                <div className="flex items-center gap-2 text-red-700 font-mono font-bold text-xs uppercase mb-3">
                  <Flame size={18} /> CHURNALISM & SENSATIONAL VALUES
                </div>
                <p className="font-ui text-sm text-ink leading-relaxed m-0">
                  {reportData.churn_analysis || "Content replication analysis complete."}
                </p>
              </div>
            </div>

            {/* Reader Takeaway */}
            {reportData.reader_takeaway && (
              <div className="border-all p-5 bg-paper flex items-start gap-3 shadow-sm">
                <ShieldCheck size={22} className="text-blue flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-mono text-xs font-bold uppercase text-muted block mb-1">VERIFICATION TAKEAWAY FOR READERS</span>
                  <p className="font-ui text-sm text-ink m-0 font-medium leading-relaxed">{reportData.reader_takeaway}</p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-8 border-all text-center text-muted font-mono text-sm bg-paper">
            Detailed AI analysis not ready yet. Still analyzing ingested articles.
          </div>
        )}
      </div>
    </div>
  );
}

