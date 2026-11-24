# Fit Rubric

Read settings.json and candidate-profile.md. This is a customizable starting rubric, not a universal hiring model. Settings own the user's weights and choices; this file owns interpretation. Only supported experience establishes qualifications. Fit, eligibility, freshness and attraction are separate.

Starting weights: required40, preferred20, domain15, trajectory10, scope10, company5. Five-point increments are a starting design, not a restriction on customized weights, ratings or exact proration. Weights total100, with required+domain positive. Do not change policy during a scout run.

## Eligibility

Apply configured title, company, compensation, employment and work-authorization constraints. Use the role's actual mandate, not colleagues' titles. Ordinary PM/Technical PM/opaque IC labels and low minimum tenure are not inherently junior. Semiconductor Product Line Manager/Product Marketing Engineer exceptions require genuine product ownership. Leadership without direct reports is not people management.

Retrieve broadly within configured countries, then verify actual work options. Resolve missing, country-only, multi-location and unclear remote labels from first-party details, including residency and mandatory offices. Headquarters or the first city cannot decide. A verified acceptable option can pass; promising unresolved options remain Review/manual checks. Soft preferences are not hard gates; exceptions require the user's choice, not assumed willingness to relocate.

For disclosed base pay, reject only when its upper bound is below the configured floor in the same currency/pay period. Unknown pay/floor stays unverified; never substitute total compensation for base. Do not annualize contracts or convert currency without checking terms and stating assumptions. Pay is feasibility and decision context, not fit points or proof of scope.

Prefer first publication over updates. Reject known postings older than freshness_days; unknown dates remain unknown. Exact known IDs, first-seen history and applied/archived dispositions do not reset on retrieval or an update. Missing full JD caps provisional scores at60; do not invent a score for an access-only check.

## Evidence Ratings

These fixed reference scales separate evidence judgments from customizable weights. A/50, B/25, D/15, T/10, S/10 and K/5 are fractions multiplied by settings.weights. Raw ratings are not weighted contributions. Changing weights does not change these scales. Changing deductions or hard gates requires a coordinated rubric/helper update, separately from weight customization.

### A: Required Qualifications, Raw 0–50

Start50; subtract3 per distinct close miss and20 per genuinely missing required capability; floor zero. Re-read each clause against evidence. Respect OR alternatives and tenure scope. Working knowledge/familiarity does not mean prior ownership unless explicitly required. Meeting an alternative is not overall domain fit. Charge each missing capability once, not repeatedly for paraphrases. Raw A<=15 remains Skip regardless of weights or interest.

Coursework, advisory work and personal projects support actual literacy/applied work, not invented shipped outcomes. Do not erase genuine software/AI evidence because another domain is stronger. Missing explicitly required hands-on production ownership cannot be rescued by an aspirational narrative; apply the clause, not a keyword gate.

### B: Preferred Qualifications, Raw 0–25

Include explicit preferences embedded anywhere in the JD. Do not invent preferences from its domain. Count distinct criteria; preserve alternatives and do not multiply examples. Genuine partial evidence counts half. Retain a compact met/partial/missing tally.

| Coverage | Raw B |
| --- | --- |
| 60%+ |20–25|
| 40–59% |12–19|
| 20–39% |5–11|
| Below20% |0–4|

Only a complete JD with no explicit preferences qualifies for B=null, preferred_status=absent and exact proration below. No neutral/free points. Incomplete/unclear evidence is preferred_status=unknown, not absence. Do not remove unmet criteria or unknown candidate evidence from denominators. For a useful provisional score with unknown preferences, B=null contributes zero as an unverified lower bound and the final score is capped at60; prefer unscored review when substantive evidence is missing.

### D: Domain Fit, Raw 0–15

Assess the actual product, customers and decisions against demonstrated experience. Strong direct evidence generally supports12–15; concrete credible transfer with a meaningful ramp7–11; weak/limited transfer0–6. These are guides, not gates. Explain the bridge. Generic PM skills, interest or an employer's AI/platform label do not establish fit. Domain points replace the former generic-domain minus15; never stack both. Retain independently required specialist deductions, but do not use D as another fixed deduction for that same clause. Strong overall transfer can coexist with a missing specialist capability.

### T: Trajectory And Interest, Raw 0–10

Use the user's desired direction, separately from existing experience in D. Include directional interest here without an extra bonus. An attractive pivot can still fail required qualifications. Do not infer user preferences from a resume or employer prestige.

### S: Actual Role Scope, Raw 0–10

Assess authority over problems, vision, roadmap, product economics, lifecycle and cross-team tradeoffs. Broad end-to-end ownership generally supports8–10; substantive bounded ownership5–7; narrow execution-only work lower. Judge mandate, not title, tenure minimum or salary. Plain PM/PM II can have substantial scope; Principal can be narrow.

### K: Company Preference, Raw 0–5

Use documented user attraction, not size or automatic prestige tiers. Default neutral3 when unknown, including new employers;4–5 for documented strong preference,0–2 for documented weaker attraction. Source priority and watch-list inclusion are not automatic fit points. Company attraction creates no professional evidence.

## Calculation And Caps

Let r,p,d,t,s,k be settings.weights. With stated preferences:

`score = r*A/50 + p*B/25 + d*D/15 + t*T/10 + s*S/10 + k*K/5`

With confirmed absent preferences in a complete JD:

`score = (r*A/50 + d*D/15) * (r+p+d)/(r+d) + t*T/10 + s*S/10 + k*K/5`

Only required and domain gain weight, preserving their ratio. With starting weights the factor is75/55: effective required600/11 and domain225/11. Do not round to55/20 or normalize every component. Use exact proration for customized weights too, including zero preferred weight. A zero required+domain denominator is invalid.

- Direct fit/credible transfer has no automatic pivot ceiling or uplift. Domain mismatch is reflected in D, not a separate penalty or a forced historical disposition.
- Raw A<=15 and other hard gates apply independently of total.
- For competitive roles whose explicit preferences define the hiring domain, coverage below half caps direct/credible-transfer fit at70 unless unusually strong specific evidence addresses it; domain mismatch caps at55. Cite actual criteria/coverage. Exactly half is not below half; a generic sole MBA preference cannot trigger the cap. No preferences means no preferred-domain cap.
- Apply the strictest applicable cap after weighting/proration, including incomplete-evidence cap60. Do not add caps to force a borderline outcome.

## Finalize

Use rubric_version=fit-v2. Retain raw A/B/D/T/S/K, preferred_status (present/absent/unknown), full_jd (true/false), weights, deductions with JD/evidence support, preferred tally, proration factor, cap and unrounded total in score_breakdown. No legacy C or generic-domain adjustment in new calculations. Preserve historical receipts; no mechanical regrading.

Use `tools/scout_io.py` validated_score(breakdown, settings["weights"]) for arithmetic, not judgment. write_lead reads weights/review_threshold from private settings. Classify using the unrounded score; show up to two decimals without rounding across a cutoff. Keep full precision in receipts.

Scores below review_threshold go to No/Skip. Eligible scores at/above it may be Apply or Review; uncertainty is not Apply-ready. Strong unscored access checks use Review in Yes. Closed/duplicate/aged records go to .archive, preserving application/contact history. No Park/Maybe queue.

Leads include score or Unscored, freshness, concise evidence-based match, up to three material gaps, resume variant, location/pay uncertainty, priority, readable listing and full JD. Detailed calculations belong in receipts, not user-facing worksheets. Scores prioritize review; they are not interview probabilities.
