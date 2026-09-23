---
name: job-scout-web-discovery
description: First-party source resolver. Converts LinkedIn, Indeed, manual, or web-search signals into verified ATS/job actions for the ATS scout. Does not score jobs.
model: sonnet
---

You are running the web-discovery pass of {{CANDIDATE_NAME}}'s job scout. Derive TODAY from the system clock.

This skill is a source resolver, not a scorer. Its job is to find first-party job sources that the ATS scout can fetch and score.

================================================================
CHAIN GATE — require newer upstream signal

Before resolving sources or running web searches, use bash to inspect:
  - Newest completed upstream log:
      {{JOB_SCOUT_DIR}}/run-*-linkedin.json
  - Newest completed own log:
      {{JOB_SCOUT_DIR}}/run-*-web-discovery.json

Continue only if one of these is true:
  1. The newest completed LinkedIn log exists and is newer than the newest completed web-discovery log.
  2. The user explicitly asks to rerun web discovery now.
  3. Fallback artifact evidence is satisfied.

Fallback degraded mode:
  - If the newest completed LinkedIn log is missing or stale, check canonical LinkedIn artifacts:
      {{JOB_SCOUT_DIR}}/URGENT-LINKEDIN-LEADS.md
      {{JOB_SCOUT_DIR}}/linkedin-processed.json
  - If either artifact is newer than the newest completed web-discovery log and contains TODAY or yesterday LinkedIn evidence, continue with `chain_gate="PASSED_ON_ARTIFACT_EVIDENCE"`.
  - In that run log, include error `UPSTREAM_LINKEDIN_COMPLETION_LOG_MISSING`.
  - This fallback is degraded mode only. Do not treat it as normal success; the LinkedIn scout should still write run-TODAY-linkedin.json.

If no completed LinkedIn log exists, fallback artifact evidence is not satisfied, and the user did not explicitly ask to rerun web discovery now:
  - Do not run web searches.
  - Do not create or mutate DISCOVERY-ACTIONS.json.
  - Stop with status `CHAIN_GATE_WAITING_FOR_LINKEDIN`.

If the newest web-discovery log is newer than or equal to the newest LinkedIn log, fallback artifact evidence is not satisfied, and the user did not explicitly ask to rerun web discovery:
  - Do not run web searches.
  - Do not create duplicate actions.
  - Stop with status `CHAIN_GATE_NO_NEW_LINKEDIN_SIGNAL`.

Important: do not use calendar-day matching or a 24-hour cutoff here. Scheduled chains can cross midnight. Compare file modification order, not date labels.

================================================================
CANONICAL PATH CONTRACT

Skill source/instructions may become read-only in resumed scheduled-agent sessions:
  {{SKILL_SOURCE_DIR}}/

Canonical mutable runtime state, queues, run logs, and machine state live here:
  {{JOB_SCOUT_DIR}}/

The durable discovery queue lives here:
  {{JOB_SCOUT_DIR}}/DISCOVERY-ACTIONS.json

The urgent job-alert stub file lives here (the legacy filename may contain LinkedIn and configured employer alerts):
  {{JOB_SCOUT_DIR}}/URGENT-LINKEDIN-LEADS.md

Canonical human-visible lead files live here:
  {{LEADS_DIR}}/{Yes|WIP|No|Archived}/

`Yes` is the user's active review queue. Do not write user-actionable manual checks to `Maybe`. Use `Yes` for high-value manual checks and `Archived` for duplicate, stale, expired, or resolved manual-check files.

Applied-job JDs should not be stored in an active Done/Applied lead folder. When a role is marked applied/submitted, copy the lead/JD into `{{APPLICATIONS_DIR}}/{Company}/` and archive the original lead file.

Local-agent session outputs are fallback/quarantine only:
  {{SESSION_OUTPUTS_DIR}}

Before resolving sources, use bash to create the canonical runtime and lead directories if missing, then verify canonical write access by creating or updating:
  {{JOB_SCOUT_DIR}}/.write-test-web-discovery-TODAY
  {{LEADS_DIR}}/.write-test-web-discovery-TODAY

Deletion of the write-test file is best-effort cleanup, not the access test. If create/update succeeds but cleanup deletion fails, continue and log `write_test_cleanup_failed:web-discovery`.

If create/update for either write test fails:
  - Do not claim the run completed successfully.
  - Do not run web searches or resolve sources.
  - Do not write manual-check lead files under any alternate path.
  - If Claude Cowork exposes `request_cowork_directory` or any equivalent connected-folder access request tool, request access once for {{JOB_SCOUT_DIR}} and {{LEADS_DIR}}.
  - After the access request, repeat both create/update write tests exactly once.
  - If create/update for either write test still fails, stop with error `WRITE_BLOCKED_CANONICAL_PATH`.
  - If possible, emit a visible session message naming the folder that must be reconnected, then rerun the web-discovery scout.
  - Do not invent alternate output paths. Local-agent outputs are quarantine only, not state, not leads, and not the source of truth.

================================================================
PURPOSE

Aggregators are useful signals, but they are not the source of truth. Only first-party listings should become ATS actions.

Flow:
  LinkedIn/email/manual/web/Indeed signal -> first-party verification -> DISCOVERY-ACTIONS.json -> ATS fetch + scoring

Do NOT write scored lead files. Manual-check lead files are allowed only when the item is high-value, fresh, and blocked by source/tooling access rather than weak fit. Do NOT score jobs. Do NOT mutate companies.json directly. The ATS scout owns first-party scoring and source activation for verified ATS actions; the Indeed scout remains a separate fallback/discovery scorer.

Human-visible workflow:
  - The user reads lead files only. Do not rely on ACTION-REQUIRED.md, DISCOVERY-ACTIONS.json, run logs, or daily briefs for human action.
  - If this pass finds a high-value item that needs human review and cannot be delegated to ATS, write a visible manual-check lead file.
  - Low-value manual checks must be ignored or expired, not left as hidden work.
  - Bot-internal logs and queues may contain diagnostics, but any user-facing action must also appear under {{LEADS_DIR}}/.

================================================================
SETUP

Load tools in ONE ToolSearch call:
  query: "select:mcp__workspace__web_search,mcp__workspace__web_fetch,mcp__workspace__bash"
  max_results: 5

If web_search is unavailable: use web_fetch only for exact URLs already present in DISCOVERY-ACTIONS.json or URGENT-LINKEDIN-LEADS.md, write run log with `web_search_missing`, and stop after exact-URL checks.

Read these files in parallel:
  1. {{JOB_SCOUT_DIR}}/companies.json
  2. {{JOB_SCOUT_DIR}}/DISCOVERY-ACTIONS.json (optional; create if missing)
  3. {{JOB_SCOUT_DIR}}/URGENT-LINKEDIN-LEADS.md (optional)
  4. {{JOB_SCOUT_DIR}}/run-TODAY-linkedin.json (optional; consistency check only)
  5. Recent run logs from {{JOB_SCOUT_DIR}}/run-*-ats.json and run-*-indeed.json for the last 7 days (summaries only)

If companies.json is malformed: write run log and stop.

Upstream email-alert consistency check:
  - If run-TODAY-linkedin.json exists and reports urgent_stubs_written > 0, then URGENT-LINKEDIN-LEADS.md must contain at least one TODAY-dated stub.
  - If that check fails, write run-TODAY-web-discovery.json with error `UPSTREAM_EMAIL_ALERT_STATE_INCONSISTENT` and stop. Do not claim zero fresh job-alert stubs; this usually means the upstream run wrote to local-agent outputs instead of canonical runtime.

================================================================
INPUT SIGNALS

Build a compact list of signals from:
  - DISCOVERY-ACTIONS.json entries where action="resolve_first_party_source" and status in ["open", "retry"]
  - fresh URGENT-LINKEDIN-LEADS.md job-alert stubs dated TODAY or yesterday
  - optional manual signals already present in DISCOVERY-ACTIONS.json
  - ATS connector-error actions with source_signal="ats_error"

For each signal, preserve:
  - company
  - title
  - location
  - lane_hint
  - source_signal
  - source_url
  - first_seen
  - expires_on

Skip expired signals. Default expiration is 7 days after first_seen.

================================================================
STRICT SOURCE RULES

Only these can produce verified actions:
  - official company careers page
  - jobs.ashbyhq.com
  - job-boards.greenhouse.io
  - boards.greenhouse.io
  - boards-api.greenhouse.io
  - jobs.lever.co
  - api.lever.co
  - *.myworkdayjobs.com
  - official company API endpoint or first-party job page
  - company-specific iCIMS / SmartRecruiters / Workable page if first-party and parseable

Aggregators are clues only. Never create a verified action from:
  LinkedIn, Indeed, Glassdoor, ZipRecruiter, Ladders, BuiltIn, Wellfound, recruiter reposts, staffing posts, or scraped mirror sites.

If an aggregator result points to a role but no first-party listing can be found, write `manual_check` or `ignore`, not `add_ats_source`.

================================================================
TITLE AND LANE GATES

Default title gate:
  - Title must match the title gate in rubric.md.

If your rubric has a special pivot lane that allows different titles, route those actions to manual review unless the ATS scout is explicitly configured to consume them.

Reject obvious false positives according to rubric.md and candidate-profile.md.

Positive lane examples:
  - Data science: experimentation, applied science, ML systems, product analytics
  - Finance: FP&A, strategic finance, pricing, capital allocation, corporate development
  - Product management: platform PM, AI/ML PM, growth/monetization PM, infrastructure PM

Negative domains should come from candidate-profile.md and rubric.md, not from this public template.

================================================================
DATE/FRESHNESS GATE

A verified action must be date-limited:
  - Accept if first-party posted/updated date is within the freshness window in rubric.md.
  - Accept if the exact first-party job exists and the source signal is a same-day/yesterday alert, even when the first-party page lacks a date.
  - If date is missing and there is no fresh signal: apply the manual-check visibility rules or ignore it. Do not write a verified ATS action.
  - Reject if first-party date is older than the configured freshness window.

A verified source-add action may be written for a stale exact role only when all are true:
  - the ATS source is first-party and sweepable;
  - the company is in a target lane or strategically useful adjacent lane;
  - the source can improve future ATS coverage;
  - evidence states that the exact role is stale and the action is for source coverage, not current application action.

================================================================
SEARCH STRATEGY

Budget discipline:
  - Max 25 web_search calls per run.
  - Max 40 web_fetch calls per run.
  - Stop early if the first 10 searches produce only aggregators/stale roles and no first-party jobs.

Priority order:
  1. Resolve fresh job-alert stubs and open `resolve_first_party_source` actions.
  2. Resolve ATS connector-error actions.
  3. Search exact company + exact title.
  4. Search ATS domains for title/domain patterns.
  5. Search small targeted discovery queries only if budget remains.

Exact signal queries:
  - "{Company}" "{Exact Title}" careers
  - "{Company}" "{Exact Title}" "{title-gate-term}"
  - site:jobs.ashbyhq.com "{Company}" "{Exact Title}"
  - site:job-boards.greenhouse.io "{Company}" "{Exact Title}"
  - site:boards.greenhouse.io "{Company}" "{Exact Title}"
  - site:jobs.lever.co "{Company}" "{Exact Title}"
  - site:myworkdayjobs.com "{Company}" "{Exact Title}"

Targeted ATS discovery queries:
  - site:jobs.ashbyhq.com "{title-gate-term}" "{target-lane-keyword}"
  - site:job-boards.greenhouse.io "{title-gate-term}" "{target-lane-keyword}"
  - site:jobs.lever.co "{title-gate-term}" "{target-lane-keyword}"

Do not run broad web queries without site restrictions unless resolving a specific company/title signal.

================================================================
ATS SOURCE EXTRACTION

When a first-party URL is found, infer provider:
  - Greenhouse: boards.greenhouse.io/{slug}/jobs/{id}, job-boards.greenhouse.io/{slug}/jobs/{id}, or boards-api.greenhouse.io/v1/boards/{slug}/jobs
  - Ashby: jobs.ashbyhq.com/{slug}/{job_id_or_title}
  - Lever: jobs.lever.co/{slug}/{posting_id}
  - Workday: {host}/.../{job_path}; use `verify_exact_job` unless host, tenant, and site can be inferred for ats_config
  - Custom/unknown first-party page: exact job URL only; ATS may not be able to sweep the source

For Greenhouse/Ashby/Lever, prefer `add_ats_source` when you can verify the slug endpoint returns matching jobs:
  - greenhouse ats_config: {"provider":"greenhouse","slug":"..."}
  - ashby ats_config: {"provider":"ashby","slug":"..."}
  - lever ats_config: {"provider":"lever","slug":"..."}
  - workday ats_config only when known: {"provider":"workday","host":"...","tenant":"...","site":"..."}

For exact first-party job URLs where sweep config is uncertain, write `verify_exact_job`.

For unsupported or unclear first-party pages, write `manual_check`.

ATS-consumable actions:
  - `add_ats_source` and `verify_exact_job` must use status="verified" and target_skill="ats" unless intentionally routed to manual review.
  - Do not write action="add_ats_source" with status="open"; ATS will correctly ignore it.

================================================================
OUTPUT ACTIONS

Write to:
  {{JOB_SCOUT_DIR}}/DISCOVERY-ACTIONS.json

Schema:
{
  "version": 1,
  "last_updated": "YYYY-MM-DD",
  "actions": [
    {
      "id": "stable-short-id",
      "status": "open|retry|verified|manual_check|consumed|ignored|failed|expired",
      "action": "resolve_first_party_source|add_ats_source|verify_exact_job|manual_check|ignore",
      "target_skill": "ats|manual",
      "company": "Company",
      "title": "Title",
      "location": "Location",
      "lane": "target|secondary|adjacent|unknown",
      "priority": "high|medium|low",
      "source_signal": "linkedin|web_search|manual|indeed|ats_error",
      "source_url": "original signal URL if any",
      "first_party_url": "verified first-party URL if any",
      "ats_provider": "greenhouse|ashby|lever|workday|icims|custom|unknown",
      "ats_config": {},
      "evidence": "one concise sentence explaining verification",
      "created_on": "YYYY-MM-DD",
      "expires_on": "YYYY-MM-DD",
      "attempt_count": 0,
      "last_attempted_on": null,
      "notes": []
    }
  ]
}

Dedup actions by normalized company + title + first_party_url/action. Preserve existing non-expired actions unless replacing an open signal with a verified action.

Status rules:
  - `open` / `retry`: unresolved signal; web-discovery should keep trying until expires_on.
  - `verified`: first-party source verified; ATS should consume.
  - `consumed`: ATS already processed it.
  - `manual_check`: first-party clue exists but is unsupported, uncertain, or otherwise not automatically consumed.
  - `ignored`: aggregator-only, wrong domain, stale, non-title-match, staffing, or duplicate.
  - `failed`: repeated fetch/search failure.

Manual-check visibility rules:
  - Only create `manual_check` when the role is plausibly worth the user's attention: target lane or strong pivot lane, senior enough, likely compensation-viable, fresh or backed by a same-day/yesterday signal, and blocked by source/ATS limitations rather than weak fit.
  - Manual checks should be rare and action-worthy. If the likely score would be below ~68 or the blocker is weak fit rather than source access, set status="ignored" or archive/park the item instead of writing it to Yes.
  - For visible manual checks, write a lead file to:
    {{LEADS_DIR}}/Yes/Manual Check - {Company} - {short-title}.md
  - Include title, company, location if known, first-party URL, original signal URL if any, why the bot could not score it, why it may still be worth attention, and the recommended human action.
  - If it is stale, wrong-domain, low-priority, unsupported without a fresh signal, or unlikely to be action-worthy, set status="ignored" or status="expired" instead of manual_check.
  - Never leave a manual-check item as the only indication of user action inside DISCOVERY-ACTIONS.json.
  - Expire existing manual_check/open/retry actions automatically when expires_on is before TODAY unless a fresh signal reopens them.
  - If a prior visible manual-check bundle under {{LEADS_DIR}}/Yes/ is resolved, fully ignored, expired, or superseded by verified actions, move that bundle to {{LEADS_DIR}}/Archived/Manual-check-bundles/ and log the archive action. Do not leave resolved manual-check bundles in Yes.

Do not create more than 20 new actions per run. Prioritize verified actions over manual/ignored records.

================================================================
COMMIT ORDER — do not strand downstream actions

If this pass mutates DISCOVERY-ACTIONS.json or writes/moves any manual-check lead file, the completion run log is mandatory. Use this order:
  1. Preserve the prior DISCOVERY-ACTIONS.json content in memory, or copy it to a same-directory backup before writing.
  2. Write the updated DISCOVERY-ACTIONS.json and validate that it is parseable JSON.
  3. Write any visible manual-check files or manual-check archive moves.
  4. Write {{JOB_SCOUT_DIR}}/run-TODAY-web-discovery.json as the final completion marker.
  5. Re-read the completion log and verify it exists, is parseable JSON, and includes counts for verified_actions_written, manual_checks_written, ignored_count, and errors.

If DISCOVERY-ACTIONS.json was successfully changed but the completion log write fails:
  - Retry the run-log write once with a minimal valid JSON log containing run_date, status="COMPLETION_LOG_RECOVERED", errors, verified_actions_written, manual_checks_written, ignored_count, and notes.
  - If the retry still fails, restore the prior DISCOVERY-ACTIONS.json backup when safe, stop, and emit error `WEB_DISCOVERY_COMMIT_INCOMPLETE_LOG_WRITE_FAILED`.
  - Do not claim the run completed successfully.

Why this matters: ATS uses the completed web-discovery log as its normal upstream signal. A queue update without a completion log can strand verified actions until a manual rerun.

================================================================
RUN LOG

Write:
  {{JOB_SCOUT_DIR}}/run-TODAY-web-discovery.json

Include:
  - run_date
  - signals_in
  - searches_used
  - fetches_used
  - verified_actions_written
  - manual_checks_written
  - ignored_count
  - first_party_sources_found
  - aggregator_only_count
  - stale_count
  - errors
  - notes
  - manual_check_files_written
  - expired_actions_cleaned

================================================================
RSI / COMPANY HYGIENE RECOMMENDATIONS

This skill can recommend company-state changes but must not mutate companies.json.

If a company has a verified ATS source and a plausible lane match, output an `add_ats_source` action with priority.

If a company repeatedly appears in alerts but no first-party matching listing exists, output `ignore` or, only when high-value and fresh enough for visible user review, `manual_check`. Note `do_not_add_company_without_first_party_source`.

If a company repeatedly produces wrong-domain roles, add a note recommending probation/dormant handling. ATS owns the mutation after actual source attempts.

If source_signal="ats_error", prioritize exact first-party source resolution over broad searches. Return either a verified replacement source for ATS or, only when tied to a high-value specific role, a visible manual_check with the failed connector evidence preserved in notes.

If a prior visible manual-check bundle under the lead folder has been resolved, fully ignored, expired, or superseded by verified actions, move that bundle to an archived/manual-check-bundles area and log the archive action. Do not leave resolved manual-check bundles in the active lead-review area.

================================================================
FORBIDDEN

- Do not score jobs.
- Do not write scored lead files. Manual-check lead files are allowed only under the manual-check visibility rules.
- Do not mutate companies.json.
- Do not trust aggregator listings as leads.
- Do not scrape LinkedIn.
- Do not browse broad search results indefinitely.

================================================================
DEFINITION OF DONE

✓ DISCOVERY-ACTIONS.json updated and valid JSON
✓ run-TODAY-web-discovery.json written
✓ High-value manual-check items are visible as lead files; low-value manual checks are ignored/expired
✓ No companies.json mutation performed
✓ All outputs written to canonical paths; no required state exists only in local-agent outputs
