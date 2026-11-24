# Welcome To Job Scout

Set up a search that reflects your evidence and choices, without turning every preference into an exclusion. Answer briefly; "unknown" is valid. Your answers and generated profile stay in a private workspace outside this repository.

## Guided Interview

An assisting agent should ask one group at a time, summarize the tradeoff, and confirm consequential choices. Do not infer a minimum salary, willingness to relocate, management preference or professional ownership from a resume alone.

1. **Work you want.** Which roles and actual responsibilities do you want? Which titles are merely company leveling? IC, people management, either, or undecided? Separate true exclusions from examples you like. Map to titles, domains and soft_preferences.
2. **Evidence you can defend.** What have you owned, delivered or influenced? Give a few concrete examples, dates, customers and outcomes. For semiconductor/hardware, distinguish architecture literacy, product definition, lifecycle and direct design ownership. For AI, distinguish literacy, modeling, product work and production deployment. For software, distinguish requirements/customer work from shipped platform/API or engineering ownership. Record applicable evidence; none of these domains is mandatory. Map to profile.summary/evidence/gaps.
3. **Credible expansion.** Where can those decisions and outcomes transfer? Which capabilities are genuinely missing, merely adjacent or not assessed? A desired pivot is not evidence, but it is not automatically a capped or rejected lead either. Map to domains.prioritize/adjacent/exclude and resume_variants.
4. **Where and how.** Which countries can you work in? Preferred metros, remote residency limits, onsite/hybrid tolerance, relocation and travel? Is each a hard constraint, soft preference or open question? Use broad retrieval followed by verification of actual work options. Do not turn city spellings or headquarters into exclusion rules. Map to geography, work_authorization and soft_preferences.
5. **Compensation and employment.** Currency, minimum base if known, benefits/equity considerations, full-time/contract preferences and any real constraints? Null floor means unknown, not zero or a guessed number. Compare disclosed upper bounds with a floor; keep undisclosed pay unverified. Map to compensation.
6. **What makes work worthwhile.** Desired authority, customer proximity, pace, mission, learning, team size or industry exposure? Decide what changes fit priority versus what truly disqualifies a role. Avoid treating prestige or attractive AI language as proof of fit. Map to soft_preferences.
7. **Sources.** Review the full company starter universe. Keep company names; enable only sources useful to your search. Records without verified connections are signals, not failed searches. Add a small set of first-party discovery queries from your actual domains. Choose any employer alerts you receive; do not search all inbox messages. Map to companies.json, discovery_queries and email-alert-sources.json.
8. **Workspace and tools.** Choose a private absolute directory and timezone. Can the agent read/write there, retrieve public web pages and parse JSON? Which connected email/Indeed tools actually expose search and detail operations? Leave optional stages disabled if unavailable. Do not store credentials here. Map to timezone and tools.
9. **Attention and effort.** How many leads can you review? What freshness window and match threshold are useful? Start with the existing bounded search/retry/page budgets. High-fidelity matches are the goal: neither exhaustive coverage nor minimum tokens is success. Revisit limits based on useful incremental leads, not one unusual failure. Map to freshness_days, review_threshold and budgets.
10. **Confirm.** Read the proposed profile and settings. Correct exaggerated claims, invented preferences, hidden hard exclusions and unknowns accidentally treated as passes. Confirm the neutral absent-preference score (default15) and explicitly authorize any email archiving. Set setup_reviewed=true only after this review. Scheduling is a separate decision after a supervised run.

## Private Evidence

Resumes and selected work samples can inform the concise scout profile, but do not copy full documents into prompts or the public repo. Reference supported facts and claim boundaries, not contact details or confidential customer names. Raw performance reviews, HR/health records and private correspondence are optional private coaching evidence, never required onboarding or default scout input. A reduced scout profile is still private; "sanitized" does not mean safe to publish.

## Create And Validate

Run the README init command. Edit the generated Instructions/settings.json. Keep the single settings file authoritative for preferences; validation derives candidate-profile.md from its profile fields. Do not hand-maintain a second conflicting profile. If a preference cannot be expressed structurally, state its exact hard/soft/unknown meaning in soft_preferences and review it with the agent.

Optional email source entry (replace sender only with one you actually approve):

```json
{
  "id": "employer-alert",
  "company": "Example Employer",
  "gmail_query": "from:jobs@example.com newer_than:2d in:inbox",
  "parser": "employer_alert",
  "archive_after_processing": false,
  "max_threads": 5
}
```

The file starts with no sources; email stays disabled until approved sources are present. Check an actual sample sender and subject: employer alert vendors may use a different domain, and "new roles" need not contain "job" or "career." Confirm message content before processing. A broad sender match is not permission to read unrelated correspondence.

Run validation. It rejects blank/unfilled required profile values, malformed state containers and email queries missing sender/label or time bounds. It does not interpret every Gmail query operator: the agent must also verify that every branch of a compound query stays inside the approved source and time window. Unknown location/pay choices are allowed but remain review questions. Validation does not prove live connector permissions.

## First Useful Result

Run the offline tests first. They create a synthetic workspace, persist a signal and verified action, retrieve mock first-party data, write a full-JD lead, update state and verify duplicate handling. Semantic qualification cases are explicit review fixtures, not a claim of model accuracy.

Then approve a small supervised run on sources relevant to you. Inspect a real lead's full JD, qualification deductions, preferred tally, work-location eligibility, pay uncertainty and source URL. Verify another run does not duplicate it. Check that failures stay visible and parsed alert emails are archived only if you authorized it. Set up unattended schedules only after this succeeds.

## Placeholder Map

| Removed personal dependency | Replacement |
| --- | --- |
| Name, biography, resume paths, private achievements | User-approved profile fields; no name required |
| Career lanes and resume variants | domains, profile.evidence/gaps/resume_variants |
| Salary, geography, authorization, employment preferences | Explicit settings, with null/unknown supported |
| Personal company rankings, outcomes, correspondence | Public company/source universe; no inherited history |
| Local absolute paths | One WORKSPACE substitution performed by init |
| Harness connector IDs and credentials | Runtime tool discovery; optional capabilities default off |
| Personal inbox sources and archive permission | Empty allowlist plus explicit permission |
| Private scores, logs and calibration examples | Empty state and synthetic developer fixtures |
| Search/retry/paging preferences | Documented starting budgets and verified connection caps |

No missing placeholder should silently remove a capability or borrow somebody else's preferences.
