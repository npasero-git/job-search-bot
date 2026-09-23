# Job Scout Scoring Rubric Template

Use this file as the public-safe starting point. Replace bracketed sections with candidate-specific context.

## Candidate Evidence Boundary

Only use the configured candidate profile, resume facts, and candidate evidence files as sources for work-history claims. Applications, interviews, interview prep, cover letters, lead files, company research, recruiter conversations, and target-company notes are not employment history.

When writing a fit summary, every experience claim should map to a stated role, project, credential, or portfolio item in the candidate profile. Target companies should be framed as application context unless the candidate profile explicitly lists them as work, consulting, or advisory experience.

## Step 1: Title Gate

The title must contain `Product Manager` case-insensitively.

Accept level prefixes such as:

- Senior
- Principal
- Staff
- Lead
- Group
- Technical
- Associate
- PM II / PM III

Reject:

- Product Lead
- Product Owner
- Product Principal without `Manager`
- Product Strategy without `Product Manager`
- Director / VP / Head-of / Chief
- Program Manager / Project Manager / TPM unless the title also clearly contains `Product Manager`

## Step 2: Hard Filters

Reject before scoring when any hard filter fails:

- Compensation: use the candidate's current configured base-salary floor. For a disclosed range, reject only when its upper bound is below that floor; retain undisclosed compensation as unverified for fit scoring.
- Location outside configured acceptable metros or remote policy.
- Company category excluded by candidate preference.
  - If a third-party recruiter or staffing post appears to describe a direct-hire role at an unnamed target-lane employer, surface for Review only and cap below Apply until the actual employer or first-party listing is verified.
- Direct people-management required when candidate wants IC roles.
- Posting older than configured freshness limit.
- Title blacklist hit.
- Exact duplicate or duplicate-template role already surfaced. When a company posts multiple roles with shared boilerplate, score the unique product surface of each role, not the repeated company boilerplate.

## Step 2.5: Freshness

Classify every candidate:

- Same-day: 0-1 days old
- Fresh: 2-4 days old
- Aging: 5-7 days old
- Unknown: unparseable date

Freshness affects priority, not fit score.

## Step 3: Scoring

Score out of 100.

### A. Required Qualifications Match: 0-50

Start at 50. Subtract:

- Close miss: -3
- Clear dealbreaker: -20

Use close miss when the candidate has strong adjacent evidence. Use dealbreaker when the required qualification is genuinely absent.

For OR-based requirements, if the candidate meets one branch but the role clearly centers on the other branch, treat it as a close miss rather than a full meet.

If required qualifications are mostly generic PM skills, a high Section A score proves eligibility, not fit. Use the Domain Fit Assessment to correct generic-qualification inflation.

### B. Preferred Qualifications Fit: 0-25

Score based on the share of preferred qualifications met:

- 60%+: 20-25
- 40-59%: 12-19
- 20-39%: 5-11
- <20%: 0-4

Preferred qualifications should be interpreted honestly. Adjacent exposure is partial credit only when a hiring manager would plausibly care.

### C. Role-Level and Strategic Fit: 0-25

Suggested components:

- Title/level alignment: 0-10
- Role scope and level: 0-10
- Company signal: 0-5

Define target lanes, adjacent lanes, and avoid lanes in `candidate-profile.md`.

If a role is centered on a specialized product surface that the candidate profile does not substantiate, cap below Apply unless the profile shows direct ownership or a strong adjacent bridge.

Adjust for clear level or scope mismatch at a large company with mature leveling. Be more flexible for startups, where titles are often compressed and scope may matter more than the label.

## Domain Fit Assessment

Apply after raw A + B + C.

First identify the actual product domain underneath the title. Generic labels can obscure a specialized developer, analytics, security, marketplace, customer-support, or other domain-specific ownership surface. Score the real ownership surface, not the label.

### Tier 1: Target Lane

The role maps directly to the candidate's strongest evidence. Score normally.

### Tier 2: Aspirational Bridge

The role is outside the core lane, but a reasonable hiring manager could see a credible pivot narrative.

Do not reduce Section A for generic required qualifications, but cap the final score:

- Strong bridge: cap at 68
- Weak bridge: cap at 55-60

Default priority: Review. Promote to Apply only when the posting is fresh, the narrative is strong, and the resume variant is clear.

### Tier 3: Domain Mismatch With Generic Requirements

If required qualifications are generic PM skills and the role domain has no credible bridge, reduce Section A by 15 before recomputing.

This prevents generic PM requirements from creating inflated scores.

### Tier 4: Hard-Skill Gap

If Section A is 15 or below because of real required-skill gaps:

- If the narrative test fails: Skip.
- If the narrative test passes and the role does not require hands-on production ownership of the missing skill: allow a capped Review.

Use the stricter cap when multiple caps apply.

## Preferred Qualifications Reality Check

At highly competitive companies, preferred qualifications often describe the actual hiring profile.

If preferred qualifications are domain-defining and the candidate meets fewer than about 50%, apply a cap rather than an additive penalty:

- Target lane: cap at 70 unless unusually strong adjacent evidence exists.
- Aspirational bridge: cap at 60-65.
- Domain mismatch: cap at 55 or lower.

Do not double-penalize. Use the strictest applicable cap.

## Specialized Domain Caps

When the role's real ownership surface depends on domain depth the candidate profile does not show, cap below Apply unless there is direct evidence or a strong adjacent bridge. These are caps, not automatic skips: a role can still surface for Review when the bridge narrative is credible and the posting is strategically useful.

## Application Priority

Every surfaced candidate should receive both score and priority:

- Apply: strong fit or strategically useful pivot, fresh enough to act.
- Review: plausible fit with meaningful gaps or uncertain level/scope value.
- Park: not a near-term application priority despite nonzero score.
- Skip: hard-filtered, score below threshold, or major required-qualification mismatch.

Do not let a high score from generic PM requirements automatically become Apply.

Before writing the lead file, sanity-check the match summary and "Why this is a fit" text against the Candidate Evidence Boundary. Rewrite or downgrade any lead whose fit depends on inferred experience.

## Candidate Background Reference

Replace this section with a concise factual profile:

- Core roles and dates:
- Strongest product domains:
- Strongest technical domains:
- Customer/user evidence:
- Launch/revenue/adoption metrics:
- Current growth or adjacent-domain evidence:
- Constraints to apply when scoring:
- Resume variants:
