import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Loader2, FileText, Globe, AlertTriangle, ArrowLeft, 
  Sparkles, Cpu, CheckCircle2, Clock, GitCompare, Flame, 
  ShieldCheck, ExternalLink 
} from 'lucide-react';
import { api } from '../api';
import type { EventDetailResponse, DriftReport, Correction, ReportResponse } from '../api';

export default function Investigation() {
  const { eventId } = useParams<{ eventId: string }>();
  const [eventData, setEventData] = useState<EventDetailResponse | null>(null);
  const [driftData, setDriftData] = useState<DriftReport | null>(null);
  const [corrections, setCorrections] = useState<Correction[]>([]);
  const [reportData, setReportData] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
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
            {eventData.articles.map(article => (
              <div key={article.id} className="border-all p-4 bg-white hover:border-ink transition-colors shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-mono text-xs font-bold text-ink uppercase">{article.source_name || "News Outlet"}</span>
                  <span className="font-mono bg-ink text-paper px-1.5 py-0.5 text-[10px] uppercase font-semibold">{article.language}</span>
                </div>
                <h4 className="font-display text-md mb-2 leading-snug">{article.title}</h4>
                {article.published_at && (
                  <span className="font-mono text-[11px] text-muted block mb-3">
                    Published: {new Date(article.published_at).toLocaleString()}
                  </span>
                )}
                <a href={article.url} target="_blank" rel="noreferrer" className="text-xs font-mono font-bold text-blue hover:underline inline-flex items-center gap-1">
                  <Globe size={12} /> READ ORIGINAL ARTICLE <ExternalLink size={10} />
                </a>
              </div>
            ))}
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
                        <span className="text-xs text-muted font-mono block mb-1">ORIGINAL CLAIM</span>
                        <p className="font-display text-md">"{sourceNode.label}"</p>
                      </div>
                      <div>
                        <span className="text-xs text-muted font-mono block mb-1">MODIFIED CLAIM ({targetNode.language || '?'})</span>
                        <p className="font-display text-md text-alert">"{targetNode.label}"</p>
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

