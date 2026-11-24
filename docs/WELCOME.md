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
7. **Sources and LinkedIn alerts.** Review the company starter universe and enable sources useful to your search. Records without verified connections are signals, not failed searches. Generate a small set of tailored LinkedIn Jobs searches and email-alert instructions using the output requirements below. Email scouting uses LinkedIn plus one general recent-job-alert search; no company-specific email setup is required. Map to companies.json, discovery_queries and email-alert-sources.json.
8. **Workspace and tools.** Choose a private absolute directory and timezone. Can the agent read/write there, retrieve public web pages and read connected email? Explain that Bot 4 requires Claude's Indeed connector in this release; leave it disabled for ChatGPT/Codex. Confirm the supported search/detail tools before enabling it in Claude. Do not store credentials here. Map to timezone and tools.
9. **Attention and effort.** How many leads can you review? What freshness window and match threshold are useful? Start with the existing bounded search/retry/page budgets. High-fidelity matches are the goal: neither exhaustive coverage nor minimum tokens is success. Revisit limits based on useful incremental leads, not one unusual failure. Map to freshness_days, review_threshold and budgets.
10. **Confirm.** Read the proposed profile and settings. Correct exaggerated claims, invented preferences, hidden hard exclusions and unknowns accidentally treated as passes. Confirm the neutral absent-preference score (default15) and explicitly authorize any email archiving. Set setup_reviewed=true only after this review. Scheduling is a separate decision after a supervised run.

## Required Output: Your LinkedIn Email Alerts

Finish onboarding with a short, user-specific table containing: alert name, exact copy-ready LinkedIn Jobs search text, location, any necessary filters, and what relevant roles it should catch. Say explicitly: **Put these searches into LinkedIn Jobs and turn on daily email alerts so Bot 1 has job emails to read.** Do not finish with generic advice to create alerts or with unfilled placeholders.

Derive the searches from the user's chosen roles and supported/adjacent domains. Include a broad title search and a few complementary domain searches; avoid combining every skill into one restrictive query. For example, a synthetic industrial-products profile could start with `product manager`, `product manager industrial automation`, and `technical product manager sensors`. These illustrate keyword searches, not mandatory searches for every user. Keep location separate from the keywords; use the approved country/region rather than an unnecessarily narrow city. Apply seniority, remote and other filters only when they reflect an actual exclusion.

For each search, have the user review the results, enable its job alert, and select daily email delivery. LinkedIn supports daily or weekly alerts delivered by email, notifications, or both; see [LinkedIn's alert settings](https://www.linkedin.com/help/linkedin/answer/a1420165). The bot reads the resulting emails, not the LinkedIn website. When a sample arrives, verify that the configured email search finds it; an enabled alert is not proof of delivery. Include the final searches and any pending delivery check in the onboarding response, alongside the saved private settings.

## Indeed: Optional Claude-Only Stage

Bot 4 is supported through **Claude's Indeed connector** in this release. There is no supported ChatGPT/Codex automation path for this bot; keep tools.indeed_enabled=false there and use bots 1-3. A ChatGPT Indeed search app may be available, but it is not a drop-in replacement for the required connector search and full-job-detail workflow.

If using Claude, connect Indeed and verify both search and complete job-detail retrieval before enabling Bot 4. If mixing hosts, use the same accessible private workspace and shared lock; otherwise omit this optional stage. Do not claim it works merely because an app is installed or mentioned. Onboarding must report either "Indeed: disabled; bots 1-3 configured" or "Indeed: Claude connector verified" based on what actually happened.

## Private Evidence

Resumes and selected work samples can inform the concise scout profile, but do not copy full documents into prompts or the public repo. Reference supported facts and claim boundaries, not contact details or confidential customer names. Raw performance reviews, HR/health records and private correspondence are optional private coaching evidence, never required onboarding or default scout input. A reduced scout profile is still private; "sanitized" does not mean safe to publish.

## Create And Validate

Run the README init command. Edit the generated Instructions/settings.json. Keep the single settings file authoritative for preferences; validation derives candidate-profile.md from its profile fields. Do not hand-maintain a second conflicting profile. If a preference cannot be expressed structurally, state its exact hard/soft/unknown meaning in soft_preferences and review it with the agent.

The email template supplies two generic searches: LinkedIn job alerts and other recent new-opening emails matched by subject phrases such as "new jobs" or "new roles." Both start with a two-day inbox window and ten-thread limit, with twenty threads total. They use shared extraction, without employer names, vendor domains or bespoke employer parsers. The general query may catch noise or miss unfamiliar subject wording; inspect sender/subject/snippets before fetching plausible alert bodies and confirm actual new openings before processing.

Review these searches with the user before enabling tools.email_enabled. Keep archiving off unless explicitly authorized globally and for that source. A user can remove the general search and keep LinkedIn only. These searches do not authorize reading recruiter replies, application-status mail or unrelated correspondence.

Run validation. It rejects blank/unfilled required profile values, malformed state containers and email queries missing sender/alert-label/job-alert-subject scope or time bounds. It does not interpret every Gmail query operator: the agent must also verify that every branch stays within the approved scope and time window. Unknown location/pay choices are allowed but remain review questions. Validation does not prove live connector permissions.

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
| Harness connector IDs and credentials | Runtime tool discovery; Claude-only Indeed; optional capabilities default off |
| Personal inbox sources and archive permission | LinkedIn plus generic recent-job-alert searches; explicit permission |
| Private scores, logs and calibration examples | Empty state and synthetic developer fixtures |
| Search/retry/paging preferences | Documented starting budgets and verified connection caps |

No missing placeholder should silently remove a capability or borrow somebody else's preferences.
