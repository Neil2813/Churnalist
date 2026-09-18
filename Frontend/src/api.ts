const API_BASE = "/api/v1";

export interface Article {
  id: string;
  title: string;
  source_name: string;
  language: string;
  published_at: string;
  url: string;
}

export interface EventResponse {
  id: string;
  title: string;
  status: string;
  article_count: number;
}

export interface EventDetailResponse extends EventResponse {
  articles: Article[];
}

export interface Claim {
  id: string;
  text: string;
  claim_type: string;
}

export interface Node {
  id: string;
  label: string;
  type: string;
  language?: string;
  date?: string;
}

export interface Edge {
  source: string;
  target: string;
  relation_type: string;
}

export interface DriftReport {
  nodes: Node[];
  edges: Edge[];
}

export interface ProvenanceNode {
  id: string;
  label: string;
  node_type: string;
  language?: string;
  source_name?: string;
  url?: string;
}

export interface ProvenanceEdge {
  id: string;
  source: string; // Note: The backend schema uses from_id, to_id, but drift uses source/target.
  from_type: string;
  from_id: string;
  to_type: string;
  to_id: string;
  relation: string;
}

export interface ProvenanceGraph {
  event_id: string;
  nodes: ProvenanceNode[];
  edges: ProvenanceEdge[];
}

export interface Correction {
  id: string;
  event_id: string;
  correction_type: string;
  original_text: string;
  corrected_text: string;
  correction_url?: string;
  detected_at: string;
}

export interface DriftHighlight {
  category: string;
  source_language: string;
  target_language: string;
  original_text: string;
  drifted_text: string;
  explanation: string;
  severity_level: string;
}

export interface CorrectionHighlight {
  original_claim: string;
  corrected_claim: string;
  updated_articles_count: number;
  outdated_articles_count: number;
  details: string;
}

export interface ReportResponse {
  id: string;
  event_id: string;
  headline: string;
  summary: string;
  accuracy_analysis?: string;
  first_publisher?: string;
  first_published_at?: string;
  churn_analysis?: string;
  key_drifts: DriftHighlight[];
  correction_status?: CorrectionHighlight;
  reader_takeaway: string;
  confidence_score: number;
  evidence_sources: any[];
  created_at: string;
}

export const api = {
  async discoverEvent(topic: string, url?: string): Promise<EventResponse> {
    const payload: any = { max_articles: 10 };
    if (url) {
      payload.seed_url = url;
    } else {
      payload.topic = topic;
      payload.keywords = topic.split(" ").filter(k => k.length > 2);
    }
    
    const res = await fetch(`${API_BASE}/events/discover`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error("Failed to discover event");
    return res.json();
  },

  async getEvent(id: string): Promise<EventDetailResponse> {
    const res = await fetch(`${API_BASE}/events/${id}`);
    if (!res.ok) throw new Error("Failed to fetch event");
    return res.json();
  },

  async listEvents(skip: number = 0, limit: number = 50): Promise<EventResponse[]> {
    const res = await fetch(`${API_BASE}/events?skip=${skip}&limit=${limit}`);
    if (!res.ok) throw new Error("Failed to fetch events");
    return res.json();
  },

  async getClaimsDrift(id: string): Promise<DriftReport> {
    const res = await fetch(`${API_BASE}/claims/event/${id}/drift`);
    if (!res.ok) throw new Error("Failed to fetch claim drift");
    return res.json();
  },

  async getProvenanceGraph(id: string): Promise<ProvenanceGraph> {
    const res = await fetch(`${API_BASE}/provenance/graph/${id}`);
    if (!res.ok) throw new Error("Failed to fetch provenance graph");
    return res.json();
  },

  async getCorrections(id: string): Promise<Correction[]> {
    const res = await fetch(`${API_BASE}/corrections/event/${id}`);
    if (!res.ok) throw new Error("Failed to fetch corrections");
    return res.json();
  },

  async getTopNews(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/news/top`);
    if (!res.ok) throw new Error("Failed to fetch top news");
    return res.json();
  },

  async triggerAnalysis(eventId: string): Promise<ReportResponse> {
    const res = await fetch(`${API_BASE}/analysis/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_id: eventId })
    });
    if (!res.ok) throw new Error("Failed to trigger analysis run");
    return res.json();
  },

  async getReport(eventId: string): Promise<ReportResponse> {
    const res = await fetch(`${API_BASE}/reports/event/${eventId}`);
    if (!res.ok) throw new Error("Failed to fetch event report");
    return res.json();
  }
};


