import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Loader2, FileText, Globe, AlertTriangle, ArrowLeft } from 'lucide-react';
import { api } from '../api';
import type { EventDetailResponse, DriftReport, Correction } from '../api';

export default function Investigation() {
  const { eventId } = useParams<{ eventId: string }>();
  const [eventData, setEventData] = useState<EventDetailResponse | null>(null);
  const [driftData, setDriftData] = useState<DriftReport | null>(null);
  const [corrections, setCorrections] = useState<Correction[]>([]);
  const [loading, setLoading] = useState(true);
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
        const [drift, corr] = await Promise.all([
          api.getClaimsDrift(id).catch(() => null),
          api.getCorrections(id).catch(() => [])
        ]);
        if (active) {
          if (drift) setDriftData(drift);
          if (corr) setCorrections(corr);
        }
      } catch (err) {
        console.error("Analysis not ready or failed:", err);
      } finally {
        if (active) setLoading(false);
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
    <div className="fade-in mt-4">
      <div className="flex justify-between items-center mb-6">
        <Link to="/stories" className="inline-flex items-center gap-2 font-ui font-semibold text-sm text-muted hover:text-ink transition-colors">
          <ArrowLeft size={16} /> BACK TO STORIES
        </Link>
        <Link to={`/provenance/${eventId}`} className="inline-flex items-center gap-2 font-ui font-semibold text-sm text-blue hover:underline">
          VIEW PROVENANCE GRAPH <Globe size={16} />
        </Link>
      </div>
      
      <div className="mb-8">
        <span className="font-mono bg-ink text-white px-2 py-1 text-xs uppercase mr-2">
          {eventData.status}
        </span>
        <h2 className="font-display inline align-middle">{eventData.title}</h2>
        <p className="text-muted mt-2">Discovered {eventData.article_count} related articles across sources.</p>
        <hr className="editorial-rule" />
      </div>

      <div className="newsroom-grid">
        {/* Left Column: Sources */}
        <div>
          <h3 className="font-display border-bottom pb-2 mb-4">SOURCES</h3>
          <div className="flex flex-col gap-4">
            {eventData.articles.map(article => (
              <div key={article.id} className="border-all p-4">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-mono text-xs text-muted">{article.source_name || "Unknown"}</span>
                  <span className="font-mono bg-blue text-white px-1 text-[10px] uppercase">{article.language}</span>
                </div>
                <h4 className="font-ui font-semibold text-sm mb-2">{article.title}</h4>
                <a href={article.url} target="_blank" rel="noreferrer" className="text-xs flex items-center gap-1">
                  <Globe size={12} /> View Source
                </a>
              </div>
            ))}
            {eventData.articles.length === 0 && (
              <p className="text-muted italic text-sm">No articles ingested yet. Still fetching live data...</p>
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
            <div className="flex flex-col gap-8">
              {driftData.edges.map((edge, idx) => {
                const sourceNode = driftData.nodes.find(n => n.id === edge.source);
                const targetNode = driftData.nodes.find(n => n.id === edge.target);
                if (!sourceNode || !targetNode) return null;

                return (
                  <div key={idx} className="evidence-strip">
                    <div className="bg-ink text-paper p-1 text-xs font-mono font-bold mb-2 uppercase flex items-center gap-2">
                      <AlertTriangle size={14} className="text-alert" /> 
                      {edge.relation_type.replace(/_/g, ' ')}
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="border-right pr-4 pl-4 pb-4">
                        <span className="text-xs text-muted font-mono block mb-1">ORIGINAL CLAIM</span>
                        <p className="font-display text-lg">"{sourceNode.label}"</p>
                      </div>
                      <div className="pr-4 pb-4">
                        <span className="text-xs text-muted font-mono block mb-1">MODIFIED CLAIM ({targetNode.language || '?'})</span>
                        <p className="font-display text-lg text-alert">"{targetNode.label}"</p>
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
            <div className="mt-12">
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
                        <p className="font-ui text-sm">{corr.corrected_text}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
