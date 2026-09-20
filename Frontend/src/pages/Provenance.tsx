import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, GitCommit } from 'lucide-react';
import { api } from '../api';
import type { ProvenanceGraph, EventDetailResponse } from '../api';

export default function Provenance() {
  const { eventId } = useParams<{ eventId: string }>();
  const [graph, setGraph] = useState<ProvenanceGraph | null>(null);
  const [eventData, setEventData] = useState<EventDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!eventId) return;

    const fetchData = async () => {
      try {
        const [ev, gr] = await Promise.all([
          api.getEvent(eventId),
          api.getProvenanceGraph(eventId)
        ]);
        setEventData(ev);
        setGraph(gr);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch provenance data.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [eventId]);

  if (error) {
    return (
      <div className="bg-alert text-white p-4 font-mono">
        <strong>Error:</strong> {error}
        <Link to="/stories" className="block mt-4 underline">Return to Stories</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="fade-in mt-4 animate-pulse">
        <div className="h-6 w-36 mb-6" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
        <div className="mb-8">
          <div className="h-8 w-2/3 mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <div className="h-4 w-40 mb-4" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
          <hr className="editorial-rule" />
        </div>
        <div className="max-w-2xl mx-auto border-left pl-8 relative ml-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="mb-12 relative">
              <div className="absolute -left-[41px] top-1 bg-paper border-all p-1 z-10 rounded-full">
                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.2 }} />
              </div>
              <div className="p-4 border-all bg-white shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <div className="h-3 w-24" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
                  <div className="h-3 w-8" style={{ backgroundColor: 'var(--color-blue)', opacity: 0.3 }} />
                </div>
                <div className="h-6 w-full mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
                <div className="h-3 w-40 mb-2" style={{ backgroundColor: 'var(--color-ink)', opacity: 0.15 }} />
                <div className="h-3 w-20" style={{ backgroundColor: 'var(--color-blue)', opacity: 0.3 }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!graph || !eventData) return null;

  // Simple sorting for visual pipeline: Articles typically come first, then claims/corrections.
  const nodes = [...graph.nodes].sort((a, b) => a.node_type.localeCompare(b.node_type));

  return (
    <div className="fade-in mt-4">
      <Link to={`/investigate/${eventId}`} className="inline-flex items-center gap-2 font-ui font-semibold text-sm mb-6 text-muted hover:text-ink transition-colors">
        <ArrowLeft size={16} /> BACK TO INVESTIGATION
      </Link>
      
      <div className="mb-8">
        <h2 className="font-display inline align-middle">{eventData.title}</h2>
        <p className="text-muted mt-2 font-mono text-sm uppercase">PROVENANCE GRAPH</p>
        <hr className="editorial-rule" />
      </div>

      <div className="max-w-2xl mx-auto border-left pl-8 relative ml-4">
        {nodes.length === 0 && (
          <p className="text-muted italic">No provenance nodes generated yet.</p>
        )}
        
        {nodes.map((node) => {
          // Find edges related to this node
          const incomingEdges = graph.edges.filter(e => e.to_id === node.id);
          
          return (
            <div key={node.id} className="mb-12 relative">
              {/* Node indicator on the line */}
              <div className="absolute -left-[41px] top-1 bg-paper border-all p-1 z-10 rounded-full">
                <GitCommit size={16} className={node.node_type === 'CORRECTION' ? 'text-corrected' : 'text-ink'} />
              </div>
              
              {incomingEdges.map(edge => (
                <div key={edge.id} className="mb-2">
                  <span className="font-mono text-[10px] bg-ink text-paper px-2 py-0.5 uppercase inline-flex items-center gap-1">
                    ↓ {edge.relation.replace(/_/g, ' ')}
                  </span>
                </div>
              ))}
              
              <div className={`p-4 border-all bg-white ${node.node_type === 'CORRECTION' ? 'border-corrected' : ''}`}>
                <div className="flex justify-between items-start mb-2">
                  <span className="font-mono text-xs font-bold uppercase text-muted">
                    {node.node_type}
                  </span>
                  {node.language && (
                    <span className="font-mono text-[10px] bg-blue text-white px-1 uppercase">
                      {node.language}
                    </span>
                  )}
                </div>
                
                <h3 className="font-display text-xl mb-2">
                  {node.label}
                </h3>
                
                {node.source_name && (
                  <p className="text-xs font-mono text-muted mb-2">Source: {node.source_name}</p>
                )}
                
                {node.url && (
                  <a href={node.url} target="_blank" rel="noreferrer" className="text-xs text-blue hover:underline">
                    View Original
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
