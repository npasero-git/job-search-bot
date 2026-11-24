# Fit Rubric

Read settings.json and candidate-profile.md. Only supported professional/project evidence establishes qualifications; interest in a company or an application does not. Fit, eligibility, freshness and personal attraction are separate.

## Eligibility

Apply configured title, company, compensation, employment and work-authorization constraints. Use the role's own mandate, not titles of colleagues mentioned in its JD. Ordinary PM/Technical PM/opaque IC labels and low minimum tenure are not inherently junior. Semiconductor Product Line Manager/Product Marketing Engineer exceptions require genuine product ownership. Leadership without direct reports is not people management.

Retrieve broadly within configured countries before evaluating actual work options. Resolve missing, country-only, multi-location and unclear remote labels from first-party details, including residency and mandatory office attendance. A genuine acceptable option can pass; headquarters or the first city alone cannot decide. Unresolved options remain Review/manual checks for promising roles, not automatic rejection or approval. Soft preferences are not hard gates; exceptions require the user's choice, not assumed willingness to relocate.

For disclosed base pay, reject only when its upper bound is below the configured floor in the same currency/pay period. Unknown pay/floor stays unverified; never substitute total compensation for base. Do not annualize contract pay or convert currency without stating assumptions and checking terms.

Prefer first publication over later updates. Reject known postings older than freshness_days; unknown dates remain unknown. Exact known IDs, first-seen history and applied/archived dispositions do not reset with retrieval time or an update. Missing full JD caps provisional scores at60; do not invent a score for an access-only check.

## Required Evidence: A (0-50)

Start50; subtract3 for each distinct close miss and20 for each genuinely missing required capability; floor zero. Re-read the actual clause against profile evidence. Respect OR alternatives and tenure scope. Working knowledge/familiarity does not mean prior ownership unless explicitly required. Meeting an alternative is not proof of overall fit. Charge a missing capability once, not repeatedly for paraphrases.

Explicit production ownership remains a gap when absent. Coursework, advisory work and personal agents can support literacy and applied work, not invented shipped outcomes. Do not erase genuine software/AI evidence because another domain is stronger.

## Preferred Evidence: B (0-25)

Identify all explicit preferences, even an MBA preference embedded in a degree requirement. Do not invent preferences from the role's domain. Count distinct criteria; preserve alternatives and do not multiply examples into requirements. Genuine partial evidence counts half. Retain a concise met/partial/missing tally and evidence in score_breakdown.

| Coverage | B |
| --- | --- |
| 60%+ | 20-25 |
| 40-59% | 12-19 |
| 20-39% | 5-11 |
| Below20% | 0-4 |

For a complete JD with no explicit preferences, use absent_preferred_score (default15), labeled "no stated preferences." This is a convention, not evidence of met preferences. Missing JD sections cannot establish absence.

## Scope And Strategic Fit: C (0-25)

Use role scope/level0-10, demonstrated domain/transfer fit0-10, and company relevance0-5. Draw from settings and evidence, not prestige alone. No overqualification penalty based solely on years or title. AI/platform labels do not establish the actual product surface. Keep specialist gaps even for attractive employers.

## Domain And Caps

- Direct fit and credible transfer: score normally; no automatic pivot ceiling or uplift. Identify the demonstrated decisions/customers/outcomes that transfer.
- Generic requirements with no credible domain bridge: subtract15 from A, floor zero. Do not stack this with an explicit specialist deduction for the same mismatch.
- A<=15: Skip. Explicit required hands-on production ownership that is genuinely absent cannot be rescued by an aspirational narrative.
- For competitive roles whose actual preferred criteria define the hiring domain, coverage below half caps direct/credible-transfer fit at70 unless unusually strong specific evidence addresses it; domain mismatch caps at55. Cite the criteria and coverage. Exactly half is not below half; a generic sole MBA preference cannot trigger this cap. No preferred criteria means no preferred-domain cap.
- Apply the strictest relevant cap, not additive penalties for the same gap. Keep incomplete-evidence cap60.

## Finalize

Recompute A from deductions, then A+B+C, domain adjustment once, and strictest cap. Retain A/B/C, deductions with JD/evidence support, preferred tally, adjustment, cap and rationale in the existing score_breakdown receipt. Use tools/scout_io.py to check arithmetic, not replace qualification judgment. Do not mechanically regrade historical records.

Scores below review_threshold go to No/Skip. Eligible scores at or above it may be Apply or Review; uncertainty does not make a role Apply-ready. Strong unscored access checks use Review in Yes. Closed/duplicate/aged records go to .archive, preserving application/contact history. No Park/Maybe queue.

The lead includes score or Unscored, freshness (Same-day0-1/Fresh2-4/Aging within window/Unknown), concise evidence-based match, up to three material gaps, resume variant, location/pay uncertainty, priority, readable listing link and complete JD. The score is prioritization judgment, not interview probability.
