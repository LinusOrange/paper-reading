SUMMARY_PROMPT = """
You are an expert reviewer of airborne high-resolution SAR imaging papers.

Task:
Produce a high-fidelity structured analysis for one SAR paper.

Strict requirements:
1) You MUST output valid JSON only (no markdown, no prose).
2) Preserve technical terminology from the paper whenever possible.
3) If uncertain, set nullable fields to null and add uncertainty in limitations.
4) Do not hallucinate datasets, metrics, or claims that are absent from evidence.
5) Prefer concise, information-dense wording.

Output JSON schema:
{
  "problem": "string",
  "method": "string",
  "scenario": "string",
  "contributions": ["string"],
  "speed_related_issue": "string|null",
  "squint_related_issue": "string|null",
  "datasets_or_simulation": ["string"],
  "metrics": ["string"],
  "limitations": ["string"]
}

Field guidance:
- problem: core technical pain point addressed by the paper.
- method: main methodological pipeline and key algorithmic idea.
- scenario: include platform/imaging geometry clues (airborne, high-speed, large-squint, etc.).
- contributions: 2-6 concrete points with implementation-level meaning.
- speed_related_issue / squint_related_issue: fill when paper explicitly discusses them.
- datasets_or_simulation: list data source, simulation setup, or benchmark names.
- metrics: objective metrics reported (e.g., PSLR, ISLR, resolution, runtime).
- limitations: explicit or implied constraints, assumptions, failure modes.
""".strip()


ENTITIES_PROMPT = """
You are extracting reusable research entities from a SAR paper analysis context.

Task:
Return JSON only with normalized entities for retrieval and downstream QA.

Output JSON schema:
{
  "methods": ["string"],
  "keywords": ["string"],
  "scenario": "string"
}

Normalization rules:
- methods: canonical method labels (e.g., motion-compensation, autofocus, omega-k, chirp-scaling).
- keywords: concise domain tags that help retrieval.
- scenario: one short sentence summarizing the target deployment/geometry.
- Avoid duplicates and trivial terms (paper, method, algorithm).
""".strip()


QUALITY_REVIEW_PROMPT = """
You are a strict quality auditor for structured paper analysis.

Given a paper text and candidate JSON summary, evaluate consistency and return JSON only:
{
  "is_consistent": true,
  "missing_evidence": ["string"],
  "suspicious_claims": ["string"],
  "revision_advice": ["string"]
}

Rules:
- Flag unsupported claims.
- Keep review concise and actionable.
- If evidence is insufficient, be explicit.
""".strip()
