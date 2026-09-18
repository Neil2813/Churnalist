"""
LLM Prompt Templates for DRIFT AI Agents.

Includes prompts for:
- Agent 2 (Claim Miner): Extracting atomic claims with spans
- Agent 3 (Event Weaver): Event candidate alignment
- Agent 4 (Drift Investigator): Multilingual claim drift classification & churnalism reasoning
- Agent 5 (Truth Trail): Evidence-first report generation
"""
from __future__ import annotations

# ── Agent 2: Claim Miner ──────────────────────────────────────────────────────

CLAIM_MINER_PROMPT = """
You are an expert news analyst assistant. Your job is to extract atomic factual claims from a news article.

Article Title: {title}
Article Language: {language}
Article Content:
{content}

Instructions:
1. Extract atomic factual claims. Each claim should represent one clear fact.
2. For each claim, return:
   - claim_type: One of [FACT, NUMBER, DATE, LOCATION, CAUSE, ATTRIBUTION, SEVERITY, CERTAINTY, QUOTE, ACTION, CASUALTY, STATUS, OTHER]
   - subject: The subject of the claim (e.g. "workers", "train", "government")
   - predicate: Action or state (e.g. "injured", "derailed", "announced")
   - object_value: The value/object (e.g. "17", "Chennai", "redevelopment plan")
   - object_unit: Unit if numerical (e.g. "people", "USD", "km/h", null if none)
   - attribution: Who reported or stated this (e.g. "police official", "spokesperson", null)
   - certainty: Degree of certainty (e.g. "confirmed", "reported", "alleged", "suspected")
   - severity: Severity level if applicable (e.g. "fatal", "minor", "serious", null)
   - raw_text: Exact or original text fragment from the article containing this claim.

Return your response strictly as a JSON object matching this schema:
{{
  "claims": [
    {{
      "claim_type": "CASUALTY",
      "subject": "workers",
      "predicate": "injured",
      "object_value": "17",
      "object_unit": "people",
      "attribution": "police officials",
      "certainty": "reported",
      "severity": "serious",
      "raw_text": "Officials said 17 workers were seriously injured in the explosion."
    }}
  ]
}}
"""


# ── Agent 3: Event Weaver ─────────────────────────────────────────────────────

EVENT_WEAVER_ALIGNMENT_PROMPT = """
Determine if the candidate article describes the exact same real-world event as the canonical event reference.

Canonical Event:
Title: {event_title}
Summary: {event_summary}
Time: {event_time}
Location: {event_location}

Candidate Article:
Title: {candidate_title}
Language: {candidate_language}
Published At: {candidate_published_at}
Snippet/Content:
{candidate_text}

Instructions:
Evaluate if both documents refer to the SAME event (e.g. same accident, same speech, same press conference) vs different events.

Return strictly as JSON:
{{
  "is_same_event": true | false,
  "confidence": 0.0 to 1.0,
  "reasoning": "Explanation of shared entities, temporal match, and location match."
}}
"""


# ── Agent 4: Drift Investigator ───────────────────────────────────────────────

DRIFT_INVESTIGATOR_PROMPT = """
Compare claims from a Source Article against claims from a Target Article (which may be in a different language or edition).

Source Article ({source_lang}):
Claims: {source_claims_json}

Target Article ({target_lang}):
Claims: {target_claims_json}

Instructions:
Categorize claim relationships and identify information drift:
Possible relation types:
- SAME: Identical factual meaning.
- MODIFIED: Value or detail changed (e.g. 17 -> 20).
- ADDED: Claim present in target but absent in source.
- DROPPED: Claim present in source but omitted in target.
- CONTRADICTS: Direct conflict.
- NUMERICAL_DRIFT: Change in numbers/quantities.
- ATTRIBUTION_LOSS: Attribution removed (e.g. "Officials said X" -> "X happened").
- SEVERITY_AMPLIFICATION: Amplified wording (e.g. "injured" -> "critically injured").
- SEVERITY_SOFTENING: Softened wording.

Return strictly as JSON:
{{
  "relations": [
    {{
      "source_claim_id": "...",
      "target_claim_id": "...",
      "relation_type": "NUMERICAL_DRIFT",
      "confidence": 0.95,
      "reason": "Source states 17 injured, target states around 20 injured."
    }}
  ]
}}
"""


# ── Agent 5: Truth Trail ──────────────────────────────────────────────────────

TRUTH_TRAIL_REPORT_PROMPT = """
You are Agent 5 (Truth Trail), a senior data journalism reasoning agent.
Synthesize all structured evidence into an objective, evidence-first provenance report.

Event Title: {event_title}
Canonical Summary: {event_summary}

Analyzed Articles ({articles_count}):
{articles_summary}

Extracted Claims & Drift Relations:
{drift_relations_summary}

Identified Corrections:
{corrections_summary}

Instructions:
1. Write a clear, objective summary of the event's reporting lifecycle across sources and languages.
2. Provide an ACCURACY ANALYSIS explaining which news sources/articles are accurate and grounded in verified facts.
3. Identify the FIRST PUBLISHER (the original source/outlet that broke the story first) and its publication timestamp if available.
4. Provide a CHURN ANALYSIS identifying who churned the news (copied without independent verification), who altered/exaggerated facts, or who spread unverified/fake values.
5. Detail key information drifts (e.g. numerical drift, attribution loss, severity changes).
6. Summarize correction status if applicable.
7. Provide a clear key takeaway for readers.

Return strictly as JSON matching this structure:
{{
  "headline": "...",
  "summary": "...",
  "accuracy_analysis": "Detailed assessment of which news article/source is accurate and evidence-grounded.",
  "first_publisher": "Name of original primary publisher/outlet",
  "first_published_at": "Original publication date/time string",
  "churn_analysis": "Breakdown of which outlets churned the news, altered claims, or spread unverified/fake values.",
  "key_drifts": [
    {{
      "category": "NUMERICAL_DRIFT",
      "source_language": "en",
      "target_language": "ta",
      "original_text": "17 workers injured",
      "drifted_text": "around 20 workers injured",
      "explanation": "Tamil edition modified the casualty figure from 17 to approximately 20.",
      "severity_level": "MEDIUM"
    }}
  ],
  "correction_status": {{
    "original_claim": "17 injured",
    "corrected_claim": "12 injured",
    "updated_articles_count": 2,
    "outdated_articles_count": 5,
    "details": "Original report of 17 injured was officially corrected to 12. 5 indexed articles still retain the original figure."
  }},
  "reader_takeaway": "...",
  "confidence_score": 0.92
}}
"""

