---
name: job-scout-indeed
description: Indeed fallback/discovery sweep. Reads ATS state, uses budgeted searches, scores known-company fallback roles, and writes source-resolution actions for new companies.
model: sonnet
---

You are running the Indeed pass of {{CANDIDATE_NAME}}'s job scout. Derive TODAY from the system clock.

Indeed is not comprehensive. Treat it as fallback and broad discovery, not as the source of truth. First-party ATS/company listings are preferred whenever available.

Human-visible workflow:
  - The user reads lead files only. Do not rely on ACTION-REQUIRED.md, DISCOVERY-ACTIONS.json, run logs, progress files, or daily briefs for human action.
  - Any job requiring user attention must be represented by a visible file under {{LEADS_DIR}}/.
  - Discovery actions are bot-to-bot queue items only. Do not create hidden human work there.

Same-day reruns are allowed. Do not stop just because run-TODAY-indeed.json already exists. Treat completed run logs as history; only resume if run-TODAY-indeed-progress.json exists and indicates an incomplete run.

================================================================
CHAIN GATE — require newer upstream signal

Before making Indeed API calls, use bash to inspect:
  - Newest completed upstream log:
      {{JOB_SCOUT_DIR}}/run-*-ats.json
  - Newest completed own log:
      {{JOB_SCOUT_DIR}}/run-*-indeed.json
  - Today's progress checkpoint, if any:
      {{JOB_SCOUT_DIR}}/run-TODAY-indeed-progress.json

Continue only if one of these is true:
  1. An incomplete run-TODAY-indeed-progress.json exists.
  2. The newest completed ATS log exists and is newer than the newest completed Indeed log.
  3. The user explicitly asks to rerun Indeed now.

If no completed ATS log exists, there is no incomplete progress checkpoint, and the user did not explicitly ask to rerun Indeed now:
  - Do not spend Indeed API budget.
  - Do not search or fetch Indeed jobs.
  - Do not write lead files.
  - Stop with status `CHAIN_GATE_WAITING_FOR_ATS`.

If the newest Indeed log is newer than or equal to the newest ATS log and there is no incomplete progress checkpoint and no explicit rerun request:
  - Do not spend Indeed API budget.
  - Do not create duplicate lead files.
  - Stop with status `CHAIN_GATE_NO_NEW_ATS_SIGNAL`.

Important: do not use calendar-day matching or a 24-hour cutoff here. Scheduled chains can cross midnight. Compare file modification order, not date labels.

================================================================
CANONICAL PATH CONTRACT

Skill source/instructions may become read-only in resumed scheduled-agent sessions:
  {{SKILL_SOURCE_DIR}}/

Canonical mutable runtime state, queues, run logs, and machine state live here:
  {{JOB_SCOUT_DIR}}/

The durable discovery queue lives here:
  {{JOB_SCOUT_DIR}}/DISCOVERY-ACTIONS.json

The urgent LinkedIn stub file lives here:
  {{JOB_SCOUT_DIR}}/URGENT-LINKEDIN-LEADS.md

Canonical human-visible lead files live here:
  {{LEADS_DIR}}/{Yes|WIP|No|Archived}/

`Yes` is the user's active review queue. Do not use `Maybe` for anything that needs user attention. Put review-worthy, high-Maybe, and unresolved/manual-check items in `Yes` with the current score or `Manual Check` in the filename. Use `Archived` for stale, duplicate, expired, or historical files.

Applied-job JDs should not be stored in an active Done/Applied lead folder. When a role is marked applied/submitted, copy the lead/JD into `{{APPLICATIONS_DIR}}/{Company}/` and archive the original lead file.

Local-agent session outputs are fallback/quarantine only:
  {{SESSION_OUTPUTS_DIR}}

Before making Indeed API calls, use bash to create the canonical runtime and lead directories if missing, then verify canonical write access by creating or updating:
  {{JOB_SCOUT_DIR}}/.write-test-indeed-TODAY
  {{LEADS_DIR}}/.write-test-indeed-TODAY

Deletion of write-test files is best-effort cleanup, not the access test. If create/update succeeds but cleanup deletion fails, continue and log `write_test_cleanup_failed:indeed`.

If create/update for either write test fails:
  - Do not spend Indeed API budget.
  - Do not fetch/score jobs.
  - Do not write or stage lead files under any alternate path.
  - If Claude Cowork exposes `request_cowork_directory` or any equivalent connected-folder access request tool, request access once for {{JOB_SCOUT_DIR}} and {{LEADS_DIR}}.
  - After the access request, repeat both create/update write tests exactly once.
  - If create/update for either write test still fails, stop with error `WRITE_BLOCKED_CANONICAL_PATH`.
  - If possible, emit a visible session message naming the folder that must be reconnected, then rerun the Indeed scout.
  - Do not invent alternate output paths. Local-agent outputs are quarantine only, not state, not leads, and not the source of truth.

================================================================
SETUP — parallel

Load tools in ONE ToolSearch call:
  query: "select:mcp__{{CONNECTOR_ID}}__{{TOOL_NAME}},mcp__{{CONNECTOR_ID}}__{{TOOL_NAME}},mcp__workspace__bash"
  max_results: 5
  If Indeed tools don't load: write run log with "indeed_tools_missing", stop.

Read these files in parallel (Read tool):
  1. {{JOB_SCOUT_DIR}}/rubric.md
  2. {{JOB_SCOUT_DIR}}/seen-jobs.json
  3. {{JOB_SCOUT_DIR}}/companies.json
  4. {{CANDIDATE_PROFILE_PATH}}
  5. {{JOB_SCOUT_DIR}}/URGENT-LINKEDIN-LEADS.md (optional; if missing, continue)
  6. {{JOB_SCOUT_DIR}}/DISCOVERY-ACTIONS.json (optional; if missing, continue)
  7. {{JOB_SCOUT_DIR}}/role-ledger.json (optional; create if missing)

If companies.json is missing, malformed, or missing its top-level `companies` array: write run log, stop.
If rubric.md is missing: stop immediately.

Candidate evidence boundary:
  - Treat rubric.md, {{CANDIDATE_PROFILE_PATH}}, and configured resume/evidence files as the only sources of candidate work-history claims.
  - Do not infer experience from Applications folders, interview-prep files, lead files, company research, recruiter messages, or prior application targets.
  - If a fit claim cannot be mapped to the candidate profile, resume, credential, project, or explicit evidence file, do not use it.
  - Target-company names are application context only unless the candidate profile explicitly lists them as work, consulting, or advisory experience.

Compensation policy:
  - Read the candidate's private compensation rule from rubric.md. Do not hard-code a number in this shared skill.
  - A disclosed base-salary range passes only when it satisfies that private rule. Retain absent or unparseable compensation for fit scoring as `Comp: Not disclosed / unverified`.

================================================================
ROLE LEDGER — cross-source dedupe

Path: {{JOB_SCOUT_DIR}}/role-ledger.json

Purpose: `seen-jobs.json` prevents exact source-ID rescoring. `role-ledger.json` prevents duplicate active lead files when the same real-world role appears through different sources, such as ATS + Indeed or an Indeed repost with a new job ID.

Load `role-ledger.json` during setup. If missing, initialize:
{
  "version": 1,
  "last_updated": "TODAY",
  "roles": []
}

For every candidate that survives metadata hard filters, compute:
- source_id / canonical_key: provider-specific ID, such as `indeed:JOBSEARCH_12345`
- normalized_company: lowercase company, punctuation collapsed
- normalized_title: lowercase title, punctuation collapsed; keep seniority words because Senior/Staff/Principal may be distinct roles
- coarse_location: normalize common metro variants where useful; otherwise use concise normalized location
- role_key: `normalized_company|normalized_title|coarse_location`

Check `role-ledger.json` in three stages:
1. Pre-score exact duplicate check: if source_id already appears in any role.source_ids, skip scoring/writing and log `ledger_exact_duplicate:{company}:{title}`.
2. Pre-score URL duplicate check: if listing_url or apply_url is already known from metadata and appears in any role.listing_urls or role.apply_urls, skip active lead creation and log `ledger_url_duplicate:{company}:{title}`.
3. Post-fetch / pre-write probable duplicate check: if role_key matches an existing role, compare product surface, req ID, and JD summary after the full JD is available.
   - If it is the same real-world role, do not create another active lead file. Update the existing ledger entry with the new source_id, listing_url, apply_url, last_seen, latest_seen_score if scored, and source history. If the new source has a fuller JD or a materially different score, append a short `## Scout Refresh` note to the existing lead_file_path instead of creating a second active file.
   - If it is genuinely a different role with the same generic title, keep it and add a disambiguating `role_key_suffix` such as req ID, product surface, or team name. Log `ledger_same_title_distinct_role:{company}:{title}`.

Do not over-suppress:
- Do not merge roles just because they share company + generic title when the team/product surface differs.
- Do not merge Senior/Staff/Principal variants automatically unless the JD text shows the same product surface and one is clearly a duplicate template or lower-level repost.
- If uncertain, write the new lead file but add `possible_duplicate_of` in the run log; uncertainty should not hide a potentially good lead.
- Stale-score exception: if an existing ledger match is older than 14 days, the JD appears materially changed, the rubric changed materially, or the role is in a target lane and the prior score was below the surface threshold, allow one rescore. Still update the existing ledger/lead file rather than creating a second active file.

Duplicate file handling:
- If a duplicate audit file is useful, write it directly to {{LEADS_DIR}}/Archived/.
- Duplicate/stale resurfaced roles should never be written to {{SKILL_SOURCE_DIR}}/leads or session output folders. Either suppress the file entirely after updating the ledger/run log, or write the audit copy directly to {{LEADS_DIR}}/Archived/.

Run logs must include: `ledger_exact_duplicates`, `ledger_url_duplicates`, `ledger_cross_source_refreshes`, `ledger_same_title_distinct_roles`, and `role_ledger_updates`.

================================================================
Read ATS coordination file:
  {{JOB_SCOUT_DIR}}/run-TODAY-ats-state.json
  If found: load ats_complete_companies, ats_broken_companies, ats_incomplete_companies, new_canonical_ids, workday_truncated, and partial/last_pass_completed if present.
  If state is partial: log "ats_state_partial:{last_pass_completed}" and treat only listed complete/incomplete/broken/truncated companies as known. Do not assume unlisted providers ran.
  If state is missing: check {{JOB_SCOUT_DIR}}/run-TODAY-ats-progress.json.
    - If progress exists, log "ats_state_missing_used_progress:{last_pass_completed}".
    - Derive workday_truncated from progress.workday_summary entries where truncated=true.
    - Leave ats_complete_companies empty unless progress explicitly lists completed companies.
    - Continue with conservative fallback coverage instead of blind full duplication.
  If neither state nor progress exists:
    - In normal scheduled-chain mode, this should already have stopped at the CHAIN GATE.
    - If the user explicitly requested an Indeed rerun without ATS state, log "ats_state_missing_explicit_rerun" and run all companies through Indeed with no skip optimization.
  Normalize workday_truncated entries by taking the company slug before any colon.
  Example: "company-slug:showing_31_unique_of_1040" counts as company "company-slug".

Read recent completed Indeed run logs from the last 7 calendar days, if available.
Use them only for lightweight anti-spam/cooldown decisions:
  - repeated zero-result company counts
  - searched_runs by company
  - repost/domain-mismatch saturation patterns
  - prior pass_1 search_result_summary entries
Do not load full historical lead files or raw JDs.

Resume check:
  {{JOB_SCOUT_DIR}}/run-TODAY-indeed-progress.json
  First check whether {{JOB_SCOUT_DIR}}/run-TODAY-indeed.json already exists and is valid JSON.
  - If the completed run log exists, treat any run-TODAY-indeed-progress.json as stale leftover from a completed run, rename it to run-TODAY-indeed-progress-STALE.json, log `completed_run_progress_ignored`, and start a same-day rerun from the beginning.
  If no completed run log exists and the progress file exists, inspect last_pass_completed.
  - If last_pass_completed is a valid unfinished pass, resume from the next uncompleted pass.
  - If last_pass_completed is "done", ignore the progress file and start a same-day rerun normally.
  - If last_pass_completed is missing, "started", or invalid, rename it to run-TODAY-indeed-progress-STALE.json, log `stale_progress_ignored`, and start from the beginning.

================================================================
CHECKPOINT — write after every pass

File: {{JOB_SCOUT_DIR}}/run-TODAY-indeed-progress.json
{
  "run_date": "YYYY-MM-DD",
  "last_pass_completed": "carry_forward|company_search|keyword_sweep|scoring|leads|done",
  "candidates": [],
  "budget_remaining": N,
  "search_result_summary": [],
  "errors": []
}

================================================================
REQUEST BUDGET

Total budget per run: 60 API calls (searches + drill-ins combined).
Track remaining budget after every API call. When budget hits 0: STOP making API calls.
Do not retry on budget exhaustion — save state and finish the run with what you have.

Budget allocation priority (execute in this order):
  1. Carry-forward drill-ins (highest ROI — these are leads we already found)
  2. Company-anchored searches (for ATS-broken and ATS-missing companies)
  3. Discovery keyword sweeps (find NEW companies not in companies.json)
  4. New drill-ins from search results

Budget reserve:
  - Preserve at least 20 API calls for Pass 2 + drill-ins after Pass 1 whenever possible.
  - Pass 1 may spend into this reserve only for carry-forward candidates, same-day LinkedIn priority hints, ATS-broken companies, or companies with recent Apply/Review/Park leads.
  - If Pass 1 reaches budget_remaining <= 20 and only ordinary curated or discovery companies remain, stop Pass 1 and move to Pass 2.
  - Do not let low-priority discovery companies consume the Pass 2 reserve.

================================================================
PASS 0 — CARRY-FORWARD

Read most recent completed Indeed run log (run-*-indeed.json, not progress files).
Recover carry_forward candidates.

For each carry-forward candidate (budget permitting):
  - Call get_job_details to retrieve full JD
  - If successful: apply hard filters, score per rubric.md
  - If rate-limited: keep in carry-forward for next run, DO NOT increment retry_count
  - If error (non-rate-limit): log error, keep in carry-forward, DO NOT add to seen_job_ids

CRITICAL: carry-forward candidates are NEVER added to seen_job_ids until they are successfully scored.
There is no retry_count limit. A lead stays in carry-forward until it is scored or the posting expires (>7 days).
If a carry-forward candidate has been stuck for 7+ days: include it in the run log under "long_stuck_unscored" with title, company, comp, and reason. Do NOT auto-discard it and do NOT create separate daily-brief cruft.

Write checkpoint.

================================================================
LINKEDIN PRIORITY HINTS (preprocessing for Pass 1, not a separate pass)

If URGENT-LINKEDIN-LEADS.md exists, parse stubs. Skip any stub dated > 1 day before TODAY.
Use stubs ONLY as priority hints — they reorder Pass 1 and drill-in queues, they do NOT
trigger separate searches. Unknown companies should be resolved by job-scout-web-discovery
before becoming ATS sources. Indeed may still search known company names as fallback, but it
is not the first-party verification layer.

For each valid stub:
  - If the stub's company is in companies.json: mark as priority_hint for Pass 1.
    Within Pass 1, process that company earlier in its bucket. Use stub title terms to
    flag which Pass 1 results deserve drill-in priority.
  - If the stub's company is NOT in companies.json: log `urgent_linkedin_orphan:{company}:{title}` and ensure DISCOVERY-ACTIONS.json has or receives a resolve_first_party_source action. Do not run an extra company search solely from the stub.

Log stub stats in the run log: total, valid, priority_hints, orphans.

================================================================
PASS 1 ANTI-SPAM / COOLDOWN POLICY — conservative, non-destructive

Purpose: preserve Indeed budget for fresh leads without overcorrecting away strategically important companies.
This is a throttle, not a permanent block.

Before Pass 1 searches, compute recent company history from the last 7 days of completed Indeed run logs:
- zero_result_runs: number of recent runs where the company returned zero results
- searched_runs: number of recent runs where the company was searched
- recent_leads: number of Apply/Review/Park lead files or surfaced candidates from that company
- recent_reposts_or_domain_drops: repeated reposts or repeated hard domain-mismatch title survivors

Temporary cooldown rule:
  - If a company has 3+ recent zero_result_runs and zero recent_leads, place it in `temporary_zero_result_cooldown` for this run.
  - Cooldown means skip the company in Pass 1 for this run only; do not mutate companies.json automatically.
  - Log every skipped company with reason and recent dates.

Overcorrection guardrails:
  - Never cooldown a company with a same-day/fresh LinkedIn priority hint.
  - Never cooldown a company with ats_broken=true; Indeed may be its only path.
  - Never cooldown a company that produced an Apply/Review/Park lead in the last 14 days.
  - For curated Tier 1 or Tier 2 companies, cooldown only every other run unless zero_result_runs >= 5. This prevents starving important targets just because Indeed indexing is bad.
  - Maintain a minimum Pass 1 search floor: if cooldown would reduce searched curated companies below 12, restore highest-tier cooled companies until at least 12 curated companies are searched.

Spam saturation candidate rule:
  - If a company repeatedly returns title survivors that are reposts or hard domain mismatches and produces zero Apply/Review leads, do not permanently block it. Log it under `spam_saturation_candidates` with evidence.
  - Suggested action should be one of: temporary cooldown, move to ATS-only if ATS coverage exists, improve company-specific keyword, or leave unchanged.

Run-log requirement:
  - Preserve counts and patterns, not raw result lists. Do not paste every search result.
  - Persist `search_result_summary` incrementally in the progress checkpoint after each company search. Do not replace the searched-company list with a note such as "not preserved across session boundary"; if a session boundary occurs, resume from the checkpointed summaries.
  - For each searched company, append a compact `search_result_summary` entry:
    {
      "company": "Name",
      "query": "Indeed query used",
      "total_results_estimate": N_or_unknown,
      "title_survivors": N,
      "reposts_detected": N,
      "metadata_hard_drops": N,
      "drill_candidates": N,
      "drilled_in": N,
      "leads_written": N,
      "zero_results": true_or_false,
      "notes": "short pattern only"
    }

Log restored companies under `restored_by_overcorrection_guardrails`.

================================================================
PASS 1 — COMPANY-ANCHORED SEARCHES

QUIET MODE: check each company's search_mode AND indeed_broken flag:
  - "full" or absent → search normally
  - "slug_only" → skip (ATS-only)
  - "paused" → skip, log
  - "dormant" → skip, log
  - "signal_only" → skip; company has not been first-party verified yet
  - "manual_watch" → skip unless a fresh exact-job signal exists
  - "blocked" → skip entirely
  - indeed_broken=true → skip, log as "indeed_broken:{company}". These companies cannot be reliably found on Indeed, often because the company name is too generic. They rely solely on LinkedIn stubs or manual discovery.
  - indeed_keywords=[] (empty) → skip, log as "no_indeed_keywords:{company}". Same as indeed_broken.

ENUMERATION (do this BEFORE any searches):
  Build the COMPLETE list of companies to search, then apply only the explicit skips below.
  Skip: companies in ats_complete_companies EXCEPT companies also listed in workday_truncated or ats_incomplete_companies.
  Skip: companies with search_mode=paused/dormant/signal_only/manual_watch/blocked, indeed_broken=true, or indeed_keywords=[].
  Skip: source_status="probation" companies if they already have verified ATS coverage and were searched by ATS today, unless ATS state says incomplete/broken.
  Skip for this run only: companies in temporary_zero_result_cooldown, subject to the overcorrection guardrails above.
  Rationale: ATS-complete companies are directly covered. Workday-truncated and ATS-incomplete companies are not fully covered and need Indeed fallback, especially when fresh signals mention roles outside the visible ATS page.

  Sort the remaining companies into buckets:
    1. Companies with ats_broken=true (ATS 404'd — Indeed is their ONLY coverage)
    2. Companies in ats_incomplete_companies OR workday_truncated (ATS exists but coverage is incomplete)
    3. Companies with ats=[] AND source="curated" (curated companies with no ATS)
    4. Companies NOT in ats_complete_companies AND source="curated" (ATS didn't run or failed)
    5. Companies with ats=[] AND source in ["linkedin_discovery","web_discovery"] (auto-discovered, lowest priority)

  Within each bucket, sort by:
    1. same-day/fresh LinkedIn priority hint first
    2. oldest or null last_searched_on first
    3. tier (1 -> 2 -> 3)
    4. company name for stable ordering
  This makes Pass 1 rotate coverage day to day without needing a separate deferred-company queue.

  Log the full enumeration in the checkpoint before starting searches, including temporary_zero_result_cooldown and restored_by_overcorrection_guardrails.
  Search non-cooled companies in buckets 1-4 until either the bucket list is complete OR budget_remaining reaches the Pass 2 reserve threshold.
  Continue below the reserve only for same-day LinkedIn priority hints, ATS-broken companies, or companies with recent Apply/Review/Park leads.
  If ordinary curated companies remain when the reserve threshold is reached, defer them and log `pass_1_deferred_for_pass_2_reserve:{company}`.
  Search bucket 5 only after higher-priority fallback/curated buckets are handled and only within the discovery cap below.
  If budget is exhausted before reaching bucket 4, that is acceptable — discovery companies are speculative and should never starve curated companies or Pass 2 discovery coverage.

For each company (budget permitting):
  search_jobs(search=company.indeed_keywords[0], location="United States")
  Company-anchored searches use "United States" because the company name self-filters results;
  city-level location can miss roles posted under nearby metros, state-level locations, or remote labels.
  Apply title pre-filter on every result: title must contain the exact phrase "product manager" (case-insensitive). Reject "product lead", "product owner", "product principal", and "product strategy" without "product manager" — these add noise in the main scout. If you maintain a separate pivot scout, configure its title gate separately.
  Apply hard filters from rubric.md Step 2 on search-result metadata (title, compensation, location, date). Apply the private compensation rule from rubric.md; keep absent or unparseable compensation as unverified.
  The rubric Step 2 location filter acts as the livability gate — only acceptable US metros pass.
  Dedupe against seen_job_ids + ATS new_canonical_ids + this run's processed list + role-ledger exact/apply-URL duplicates. For role-ledger probable cross-source duplicates, refresh the existing lead file/ledger instead of creating a second active or staging lead file.
  REPOST DETECTION: Indeed often resurfaces the same role with a new job ID. Suppress reposts at two levels:
    Level 1 (within-run): skip exact canonical-key matches, exact apply-URL matches, and exact normalized (company_lower + title_lower + location) matches within this run's processed list.
    Level 2 (cross-run): before entering the drill-in queue, check each candidate's (company_lower, title_lower) pair against candidates from the 2 most recent completed Indeed run logs. If a match exists and the prior score was Skip or Park below the surface threshold, suppress the candidate. Log as `repost_suppressed:{company}:{title}:{prior_score}`.
    Exception 1 (borderline): if a prior match scored near the review threshold, do not suppress; rescore in case the role or context changed.
    Exception 2 (target-lane escape hatch): if the candidate's title contains target-lane signals configured in candidate-profile.md or rubric.md, do not suppress even if the prior score was low. Log as `repost_target_lane_rescore:{company}:{title}:{prior_score}` instead of suppressing.
    Exception 3 (staleness): if the prior match is more than 7 days old based on run-log date, do not suppress.
  Do not load full historical lead files for this check — use only the candidates[] array from recent run logs.

  DISCOVERY COMPANY CAP: search at most 5 linkedin_discovery/web_discovery companies per run.
  Sort by discovery_priority first (high → medium → low), then by linkedin_mention_count
  descending (companies LinkedIn keeps surfacing are more likely actively hiring), then
  by added_on (newest first).
  If more than 5 are pending, search only the top 5.
  Skip "low" priority discoveries entirely if budget remaining is < 20.
  Legacy cleanup guardrail: if a discovery company has ats=[] and surface_count=0 and last_searched_on is 14+ days old, skip it for this run and log `legacy_discovery_zero_yield:{company}`. Do not mutate companies.json from Indeed.
  A fresh LinkedIn stub or verified DISCOVERY-ACTIONS entry can still revive it.
  Log any skipped discoveries as "linkedin_discovery_deferred:{company}:{priority}".

Write checkpoint.

================================================================
PASS 2 — KEYWORD SWEEP

Generate keyword × location search pairs from companies.json's `indeed_config.pass_2_pm_anchored`
if configured. If that config is missing, derive a small set of keyword × location pairs from the
candidate's target and secondary lanes in candidate-profile.md. Each keyword should target a
distinct industry vertical relevant to the candidate's lane definitions — do not enumerate
variations of the same term.
Skip if budget < 15 remaining.

COMPANY EXCLUSIONS (Pass 2 only):
  Purpose: Pass 2 discovers NEW companies not in companies.json. Every company in companies.json
  is already covered — either by ATS directly or by Pass 1's company-anchored search. Excluding
  them frees result slots for novel discoveries that would otherwise be buried behind
  already-covered companies.

  Build exclusion list (two layers, in this order):
    Layer 1 (mandatory): ALL companies with configured ATS (ats[] is non-empty). These are
    directly covered by the ATS sweep — Indeed must never duplicate this work.
    Layer 2 (budget permitting): ALL remaining companies in companies.json that have
    indeed_keywords (i.e., are searchable on Indeed). These are covered by Pass 1.
    Exception: skip companies with indeed_broken=true or indeed_keywords=[] — excluding
    unsearchable names wastes a query term.

  Append exclusion terms for already-covered companies to every Pass 2 search query using
  Indeed negative-keyword syntax: `-CompanyA -CompanyB -DistinctiveWord`.
  Use each company's display name (the `name` field from companies.json).
  For multi-word names, use the most distinctive single word when needed.
  No hard cap — 25+ exclusion terms tested and working. Include all eligible companies.
  Log excluded companies in the run log.

For each search (budget permitting):
  search_jobs(search=keyword + " " + exclusion_suffix, location=location)
  Apply title pre-filter, hard filters, dedupe — same as Pass 1, including role-ledger cross-source duplicate checks.

PRE-DRILL-IN FILTER (Pass 2 results only):
  Before entering drill-in queue, every Pass 2 result must pass:
  1. Title contains "product manager" (case-insensitive). No exceptions.
  2. Posted ≤ 7 days ago. Unknown date → keep.

NEW-COMPANY SOURCE RESOLUTION:
  Pass 2 exists to discover companies not already covered by ATS or company-anchored
  searches. For every Pass 2 result that survives the pre-drill-in filter and whose
  normalized company is NOT already in companies.json:
    - Add the result to the normal drill-in queue if budget permits, because Indeed is
      still allowed to score fallback candidates.
    - Also create or update a DISCOVERY-ACTIONS.json entry so job-scout-web-discovery can
      verify the first-party source before the company becomes a recurring ATS target.

  Use this action shape:
  {
    "id": "indeed-{normalized-company}-{normalized-title}",
    "status": "open",
    "action": "resolve_first_party_source",
    "target_skill": "ats",
    "company": "{Company}",
    "title": "{Title}",
    "location": "{Location}",
    "lane": "unknown",
    "priority": "medium",
    "source_signal": "indeed",
    "source_url": "{indeed_url_or_apply_url_if_available}",
    "first_party_url": null,
    "ats_provider": "unknown",
    "ats_config": {},
    "evidence": "Indeed result passed title/date metadata gates; requires first-party verification before recurring ATS coverage.",
    "created_on": "TODAY",
    "expires_on": "TODAY+7 days",
    "attempt_count": 0,
    "last_attempted_on": null,
    "notes": []
  }

  Dedup by normalized company + title + source_signal. If an open action already exists,
  refresh last_seen/notes instead of adding a duplicate.

Write checkpoint.

================================================================
DRILL-IN

After all searches complete, collect candidates that survived hard filters and need full JD for scoring.

Prioritize drill-ins by:
  1. LinkedIn priority-hint matches first (company + overlapping title terms from stubs), ordered by freshness
  2. Then freshness: posted 0-2 days ago, then 3-5 days ago, then 6-10 days ago, then older/unknown
  3. Then likely role-lane fit from title/company keywords — prioritize titles and companies
     that map to target or secondary lanes in candidate-profile.md; deprioritize titles that
     map to avoid lanes or domain-mismatch patterns in rubric.md
     Generic examples:
       - Data science search: prioritize "Data Scientist, Experimentation" over "Reporting Analyst".
       - Finance search: prioritize "Strategic Finance" or "FP&A" over "Payroll Operations".
       - Product management search: prioritize "Product Manager, Data Platform" over
         "Program Manager, Internal Operations" or "Product Owner" if those are excluded.
  4. Then Tier 1 company candidates
  5. Then comp_upper descending
  6. Then posting date (most recent first)

For each candidate (budget permitting):
  Call get_job_details(job_id)
  - Success: score using rubric.md Step 3
  - Before writing a lead file, sanity-check fit claims against the candidate evidence boundary. Remove or rewrite any claim that treats application targets, interview history, recruiter notes, company research, or lead files as experience.
  - Rate-limited: add to carry-forward. Do NOT add to seen_job_ids.
  - Other error: add to carry-forward. Do NOT add to seen_job_ids.
  - First rate limit → STOP all drill-ins. Remaining go to carry-forward.

Write checkpoint.

================================================================
URL POLICY — visible links must open readable listings

Every lead file must include a primary `Listing` URL that opens the readable job description page. Do not make the visible primary link an apply/login/session URL.

Indeed-specific rules:
  - `to.indeed.com` links are not listing URLs. Never write them as `Listing`.
  - If Indeed job details include a company/first-party job URL, use that as `Listing`.
  - If the company has configured ATS coverage, try to resolve the job to the first-party ATS listing before writing the lead file.
  - If no first-party listing can be resolved, write `**Listing:** Unresolved - Indeed redirect only` and put the Indeed redirect under `**Source URL:**`.
  - Some official career URLs include words like `applications` in readable listing paths. They are valid Listing URLs when they open the public job description without a login/session.
  - If apply_url is a true login/session/apply-form endpoint, write `**Apply:** Apply through listing page` instead of exposing the login URL.

================================================================
LEAD FILES — write and disposition every candidate with score ≥ 50

Path: {{LEADS_DIR}}/{Yes|No|Archived}/{score}. {Company} - {short-title}.md
  - company-slug: lowercase, hyphens for spaces
  - abbreviated-title: lowercase, hyphens, max 40 chars
  Create disposition directories with bash `mkdir -p` if needed.

Folder rules:
  - Apply, Review, high-Maybe, or visible Manual Check -> {{LEADS_DIR}}/Yes/. As a default guardrail, scored leads generally need score >= 68 or clear strategic/manual-check urgency to stay in Yes.
  - Do not write Park-only leads to Yes just because they score >= 50. Park-only leads go to {{LEADS_DIR}}/Archived/Maybe-parked/ unless they are kept in No for calibration.
  - Do not use Maybe as an active queue; if a role is not worth user attention, use No or Archived.
  - Skip/below-threshold audit files -> {{LEADS_DIR}}/No/
  - duplicate/stale/expired audit files -> {{LEADS_DIR}}/Archived/

Content:
---
# {Title} @ {Company}
**Score:** {N}/100
**Freshness:** {Same-day | Fresh | Aging | Unknown}
**Location:** {location}
**Comp:** {$LOWER–$UPPER | "Not disclosed"}
**Posted:** {YYYY-MM-DD}
**Source:** indeed:{job_id}
**Listing:** {listing_url_or_"Unresolved - Indeed redirect only"}
**Apply:** {apply_url_or_"Apply through listing page"}
**Source URL:** {indeed_url_if_no_listing_or_source_context}
**Scouted:** {TODAY}

## Why this is a fit
{one sentence citing specific qualification overlaps from rubric evaluation}

## Gaps
- {gap 1}
- {gap 2}
- {gap 3}

## Recommended resume
{{RESUME_VARIANT_1}} / {{RESUME_VARIANT_2}} / {{RESUME_VARIANT_3}}

## Application priority
{Apply / Review / Park / Skip}

## Caveat
{optional caveat from rubric; omit section if none}

## Full job description
{PASTE THE COMPLETE JD TEXT HERE — every section, every bullet, every line.
 Store the JD text in a variable during drill-in, then write it to the lead file
 using bash. Do NOT summarize, shorten, paraphrase, reformat, or omit ANY part.
 Do NOT skip "boilerplate" like EEO statements, benefits, or company descriptions.
 The user needs the ENTIRE posting exactly as it appears on Indeed.
 If the JD is 3000 words, the lead file should contain all 3000 words.}
---

If get_job_details returned no description: still write the lead file but note
"JD not retrieved — apply link above" in place of the description. Do NOT skip the lead file.

================================================================
DAILY-BRIEF.md

Do not write DAILY-BRIEF.md. Lead files are the human source of truth. Run logs are machine-readable diagnostics and should contain new leads, LinkedIn priority-hint stats, carry-forward count, budget usage, pass_2_exclusions, and long_stuck_unscored if applicable.

================================================================
STATE UPDATE (after lead files written)

1. Append SCORED candidates' canonical_keys to seen_job_ids. NEVER add unscored/rate-limited/errored candidates.
2. Update role-ledger.json for every scored, refreshed, suppressed duplicate, and distinct same-title candidate:
   - new non-duplicate role -> append ledger entry with role_key, display title/company, current_folder, lead_file_path, score, priority, source_ids, listing_urls, apply_urls, first_seen, last_seen
   - duplicate/refresh -> update existing source_ids/listing_urls/apply_urls/last_seen/latest_seen_score and source history; append `## Scout Refresh` to the existing lead_file_path when useful
   - distinct same-title role -> add role_key_suffix and log why it was kept separate
   Validate JSON after writing. If validation fails, restore prior role-ledger.json and log failure.
3. Write seen-jobs.json.
4. Update companies.json: surface_count/last_surfaced_on.
   For linkedin_discovery companies that were searched this run: set last_searched_on=TODAY.
   This is lifecycle metadata; do not mark companies dormant before they have actually
   been searched or fetched by at least one downstream scout.
5. Update DISCOVERY-ACTIONS.json if new-company source-resolution actions were created or refreshed.
   - Expire or ignore invalid legacy queue items with unsupported statuses.
   - Expire open/retry/manual_check actions whose expires_on is before TODAY unless a fresh same-company/same-title signal reopens them.
   Validate JSON after writing. If validation fails, restore the prior file and log
   "discovery_actions_write_failed".
6. Write run log: {{JOB_SCOUT_DIR}}/run-TODAY-indeed.json
   Include: funnel stats, candidates (scored), carry_forward (for next run), errors, budget usage,
   linkedin_priority_hints (total, valid, matched), pass_2_exclusions (list of excluded companies),
   search_result_summary, temporary_zero_result_cooldown, restored_by_overcorrection_guardrails,
   pass_2_query_location_pairs_searched, spam_saturation_candidates, discovery_actions_created,
   ledger_exact_duplicates, ledger_url_duplicates, ledger_cross_source_refreshes,
   ledger_same_title_distinct_roles, and role_ledger_updates.
7. Delete progress checkpoint.

Carry-forward: include job_id, title, company, location, comp, posted_on, source, first_seen, reason in the run log's carry_forward array. first_seen tracks entry date for detecting stuck candidates.

================================================================
RULES

- Never add unscored candidates to seen_job_ids.
- Never silently drop a candidate after full drill-in. Metadata/title/date hard-filter drops may be summarized in the run log; candidates with fetched full JDs must be scored, carried forward, or listed as unscored/error-blocked.
- Hidden logs and queues are not a user interface. If user action is required, write a visible lead file.
- Never sleep > 15s. Budget is a hard cap. A partial run that preserves state > a complete run that drops leads.
- Rate limit on searches → skip to next pass. Rate limit on drill-ins → stop all drill-ins.
- FORBIDDEN: LinkedIn, Glassdoor, ZipRecruiter, web search, browser automation.

================================================================
DEFINITION OF DONE
✓ Lead files or duplicate suppressions, seen-jobs.json, role-ledger.json, DISCOVERY-ACTIONS.json if updated, companies.json, run log all written
✓ No files exist under {{SKILL_SOURCE_DIR}}/leads; all visible leads are in {{LEADS_DIR}} disposition folders
✓ All outputs written to canonical paths; no required state exists only in local-agent outputs
✓ Progress checkpoint deleted
