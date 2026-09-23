---
name: job-scout-ats
description: ATS-direct sweep (Workday, Greenhouse, Ashby, Lever, iCIMS). Consumes verified discovery actions, scores first-party jobs, writes lead files, and writes ATS state for the Indeed pass.
---

You are running the ATS pass of {{CANDIDATE_NAME}}'s job scout. Derive TODAY from the system clock.

Same-day reruns are allowed. Do not stop just because run-TODAY-ats.json already exists. Treat completed run logs as history; only resume if run-TODAY-ats-progress.json exists and indicates an incomplete run.

================================================================
CHAIN GATE — require newer upstream signal

Before fetching or scoring jobs, use bash to inspect:
  - Newest completed upstream log:
      {{JOB_SCOUT_DIR}}/run-*-web-discovery.json
  - Durable discovery queue:
      {{JOB_SCOUT_DIR}}/DISCOVERY-ACTIONS.json
  - Newest completed own log:
      {{JOB_SCOUT_DIR}}/run-*-ats.json
  - Today's progress checkpoint, if any:
      {{JOB_SCOUT_DIR}}/run-TODAY-ats-progress.json

Also inspect DISCOVERY-ACTIONS.json content, not only its mtime. Count due ATS-consumable actions:
  - status="verified"
  - action is "add_ats_source" or "verify_exact_job"
  - target_skill is "ats" or missing
  - expires_on is missing, TODAY, or later

Continue only if one of these is true:
  1. An incomplete run-TODAY-ats-progress.json exists.
  2. The newest completed web-discovery log exists and is newer than the newest completed ATS log.
  3. DISCOVERY-ACTIONS.json is newer than the newest completed ATS log AND contains at least one due ATS-consumable verified action.
  4. The user explicitly asks to rerun ATS now.

If no completed web-discovery log exists, there is no incomplete progress checkpoint, there are no due ATS-consumable verified actions newer than the newest ATS log, and the user did not explicitly ask to rerun ATS now:
  - Do not fetch ATS APIs.
  - Do not score jobs.
  - Do not write lead files.
  - Stop with status `CHAIN_GATE_WAITING_FOR_WEB_DISCOVERY`.

If the newest ATS log is newer than or equal to the newest web-discovery log, DISCOVERY-ACTIONS.json does not contain newer due ATS-consumable verified actions, there is no incomplete progress checkpoint, and there is no explicit rerun request:
  - Do not fetch ATS APIs.
  - Do not create duplicate lead files.
  - Stop with status `CHAIN_GATE_NO_NEW_WEB_DISCOVERY_SIGNAL`.

Important: do not use calendar-day matching or a 24-hour cutoff here. Scheduled chains can cross midnight. Compare file modification order, not date labels. Do not let open/retry/ignored/manual_check/expired/consumed actions bypass the chain gate; only due verified ATS actions are fallback upstream signal.

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

Before fetching or scoring jobs, use bash to create the canonical runtime and lead directories if missing, then verify canonical write access by creating or updating:
  {{JOB_SCOUT_DIR}}/.write-test-ats-TODAY
  {{LEADS_DIR}}/.write-test-ats-TODAY

Deletion of write-test files is best-effort cleanup, not the access test. If create/update succeeds but cleanup deletion fails, continue and log `write_test_cleanup_failed:ats`.

If create/update for either write test fails:
  - Do not fetch/score jobs.
  - Do not write or stage lead files under any alternate path.
  - If Claude Cowork exposes `request_cowork_directory` or any equivalent connected-folder access request tool, request access once for {{JOB_SCOUT_DIR}} and {{LEADS_DIR}}.
  - After the access request, repeat both create/update write tests exactly once.
  - If create/update for either write test still fails, stop with error `WRITE_BLOCKED_CANONICAL_PATH`.
  - If possible, emit a visible session message naming the folder that must be reconnected, then rerun the ATS scout.
  - Do not invent alternate output paths. Local-agent outputs are quarantine only, not state, not leads, and not the source of truth.

================================================================
SETUP — parallel

Load tools in ONE ToolSearch call:
  query: "select:mcp__workspace__bash,mcp__workspace__web_fetch"
  max_results: 5

Read these files in parallel (Read tool):
  1. {{JOB_SCOUT_DIR}}/rubric.md
  2. {{JOB_SCOUT_DIR}}/seen-jobs.json
  3. {{JOB_SCOUT_DIR}}/companies.json
  4. {{CANDIDATE_PROFILE_PATH}}
  5. {{JOB_SCOUT_DIR}}/URGENT-LINKEDIN-LEADS.md (optional; if missing, continue)
  6. {{JOB_SCOUT_DIR}}/DISCOVERY-ACTIONS.json (optional; if missing, continue)
  7. {{JOB_SCOUT_DIR}}/role-ledger.json (optional; create if missing)

If companies.json is missing, malformed, or missing its top-level `companies` array: write ACTION-REQUIRED.md entry, write run log, stop.
If rubric.md is missing: stop immediately — scoring cannot proceed without it.

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

Purpose: `seen-jobs.json` prevents exact source-ID rescoring. `role-ledger.json` prevents duplicate active lead files when the same real-world role appears through different sources, such as Greenhouse + Indeed or a repost with a new job ID.

Load `role-ledger.json` during setup. If missing, initialize:
{
  "version": 1,
  "last_updated": "TODAY",
  "roles": []
}

For every candidate that survives metadata hard filters, compute:
- source_id / canonical_key: provider-specific ID, such as `greenhouse:company:12345` or `indeed:JOBSEARCH_12345`
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
DISCOVERY ACTION INPUT

If DISCOVERY-ACTIONS.json exists, parse actions into `discovery_actions`.

ATS consumes ONLY actions where:
  - status="verified"
  - action is "add_ats_source" or "verify_exact_job"
  - target_skill is "ats" or missing
  - expires_on is TODAY or later

Ignore unresolved signals where action="resolve_first_party_source" or status="open"; those belong to job-scout-web-discovery.

Build a `verified_discovery_queue` before normal provider sweeps:
  - Sort by priority high → medium → low, then by soonest expires_on, then by source_signal freshness.
  - Consume verified `verify_exact_job` actions first because they point to specific roles.
  - Then consume verified `add_ats_source` actions, bounded to 10 source-add probes per run so the ATS pass does not become an unbounded discovery crawl.
  - If more verified actions remain after the bounded pass, leave them status="verified" and log `discovery_actions_deferred` with id, company, action, priority, and expires_on.
  - Do not let the normal company sweep start until all due exact-job actions and the bounded source-add queue have been attempted.
  - Do not mark an action consumed merely because it was loaded. It is consumed only after the exact job was scored/handled, or the source was probed and queued/scored.

For `add_ats_source` actions:
  - Require a first-party source and ats_config for a supported provider: greenhouse, ashby, lever, workday, or explicitly configured custom/icims.
  - Probe the ATS endpoint once before mutating companies.json.
  - A probe is valid only if it returns parseable jobs or the exact discovered role. Do not add a company from a 404, empty, blocked, or unparseable source.
  - If probe returns valid jobs or the exact discovered role, add/update the company in companies.json:
      source="web_discovery" if new
      source_status="probation"
      source_status_since=TODAY
      probation_attempts=0
      ats=[ats_config]
      indeed_keywords=["{Company} {title-gate-term}"] unless indeed_broken=true
      category set from lane when available
      note includes first_party_url and discovery evidence
  - If the company already exists, append ats_config only if not duplicate, and preserve curated tier/category unless missing.
  - Process the verified source early in the appropriate ATS provider pass.
  - Mark action status="consumed" only after the source has been probed and queued or scored.

For `verify_exact_job` actions:
  - Fetch the exact first-party URL.
  - If the exact source_id/canonical_id is already in seen-jobs.json, do not create a new active lead file. Update the role-ledger/source history and mark the action consumed with `consumed_note="already_seen_refreshed"` unless the JD materially changed or the existing lead is stale and intentionally being refreshed.
  - If the full JD can be retrieved, create a single candidate and score it normally.
  - If the exact page is first-party but unsupported/unparseable, log `discovery_manual_check_required:{company}:{title}` and leave action status="manual_check".
  - If an existing bundled manual-check file under {{LEADS_DIR}}/Yes/ has been resolved, fully ignored, expired, or superseded by ATS scoring, move it to {{LEADS_DIR}}/Archived/Manual-check-bundles/ and log the archive action.

Manual-check visibility:
  - If a verified exact-job action cannot be parsed but is plausibly high-value and fresh, write a visible file:
    {{LEADS_DIR}}/Yes/Manual Check - {Company} - {short-title}.md
  - Include the first-party URL, original signal URL if any, the fetch/parse failure, why it may be worth attention, and the recommended human action.
  - ACTION-REQUIRED.md, run logs, and DISCOVERY-ACTIONS.json are bot-internal. They must not be the only place where user action is required.

Do not use web search here. ATS can fetch only verified first-party URLs or configured ATS endpoints supplied by job-scout-web-discovery.

URGENT LINKEDIN INPUT

If URGENT-LINKEDIN-LEADS.md exists, parse stubs into `urgent_linkedin_stubs`:
- date
- title
- company
- location
- likely_resume
- why_it_may_fit

Skip any stub whose date is more than 1 day before TODAY. The LinkedIn skill overwrites
this file nightly, so stale stubs should be rare, but this guard prevents wasting budget
or priority-reordering on leftovers if the LinkedIn run failed or was skipped.

Use these stubs as priority hints only. Do NOT fetch LinkedIn URLs, scrape LinkedIn, or trust the stub as a scored lead.
A matching ATS candidate must still pass hard filters, fetch the full JD, dedupe, and score normally.
If a stub company exists in companies.json and has a configured ATS, process that company early within its provider pass.
If a stub company is unknown to companies.json, do not invent ATS slugs here; job-scout-web-discovery must verify a first-party source and write a verified discovery action first.
If a stub title/company matches a surfaced ATS candidate, mark it in the run log as `urgent_linkedin_matched:{company}:{title}` and prioritize scoring/drill-in ahead of non-urgent candidates.

Resume check:
  {{JOB_SCOUT_DIR}}/run-TODAY-ats-progress.json
  First check whether {{JOB_SCOUT_DIR}}/run-TODAY-ats.json already exists and is valid JSON.
  - If the completed run log exists, treat any run-TODAY-ats-progress.json as stale leftover from a completed run, rename it to run-TODAY-ats-progress-STALE.json, log `completed_run_progress_ignored`, and start a same-day rerun from the beginning.
  If no completed run log exists and the progress file exists, inspect last_pass_completed.
  - If last_pass_completed is a valid unfinished pass, resume from the next uncompleted pass.
  - If last_pass_completed is missing, "started", or invalid, rename it to run-TODAY-ats-progress-STALE.json, log `stale_progress_ignored`, and start from the beginning.

================================================================
CHECKPOINT — write after every pass

File: {{JOB_SCOUT_DIR}}/run-TODAY-ats-progress.json
{
  "run_date": "YYYY-MM-DD",
  "last_pass_completed": "workday|greenhouse|ashby|lever|icims|scoring|leads|done",
  "candidates": [],
  "errors": []
}

Also write/update a partial ATS state file after every provider pass:
  {{JOB_SCOUT_DIR}}/run-TODAY-ats-state.json

Minimum partial-state schema:
{
  "run_date": "YYYY-MM-DD",
  "partial": true,
  "last_pass_completed": "workday|greenhouse|ashby|lever|icims|scoring|leads|done",
  "ats_complete_companies": [],
  "ats_broken_companies": [],
  "ats_incomplete_companies": [],
  "new_canonical_ids": [],
  "workday_truncated": []
}

Rationale: bad network or tool failures can interrupt ATS mid-run. Indeed reads ATS state, not ATS progress, so partial state prevents fallback searches from operating blind when ATS dies after one provider pass.

================================================================
ATS SWEEP

CONTEXT EFFICIENCY: never load raw ATS JSON into LLM context. Use bash to fetch → extract → return only PM-title lines.

TITLE PRE-FILTER (applied in every bash extraction script):
  Pass postings where the title contains the exact phrase "product manager" (case-insensitive).
  Reject "product lead", "product owner", "product principal", and "product strategy" without "product manager" — these rarely map cleanly enough and add noise.
  This matches the tightened title gate in rubric.md Step 1.

Load companies from companies.json's top-level `companies` array.

QUIET MODE: check each company's search_mode field:
  - "full" or absent → fetch normally
  - "slug_only" → ATS only, skip Indeed for this company
  - "paused" → skip entirely, log "company_paused:{name}"
  - "dormant" → skip, log "company_dormant:{name}"
  - "manual_watch" → skip unless there is a same-day verified exact-job action, log "company_manual_watch:{name}"
  - "blocked" → skip entirely, log "company_blocked:{name}"
  - "signal_only" → skip; company has not been first-party verified yet
  Check search_mode_until date: if set and today > that date, treat as "full".

SOURCE LIFECYCLE STATES:
  - signal_only: company is a lead source signal only; do not fetch daily until first-party source is verified.
  - probation: newly verified ATS source; fetch for up to 3 attempts and evaluate yield.
  - active: verified source with relevant title survivors or scored leads.
  - dormant: temporarily suppressed after repeated zero-yield probation attempts; do not fetch until search_mode_until expires.
  - manual_watch: source is plausible but unsupported, unstable, or noisy; only exact verified jobs should revive it.
  - blocked: source should not be searched due to persistent bad data, irrelevant results, or known breakage.

CONNECTOR RSI / SAFE SELF-REPAIR:
  The ATS scout may repair fetch configuration when the evidence is deterministic and first-party.
  Do not change scoring, title gates, salary rules, or company priority as "repair".

  Safe repairs to attempt before marking a company broken/incomplete:
    - web_fetch or LLM-context truncates/parses a large JSON API poorly -> retry same URL with bash curl and local Python parsing. If successful, set ats[].fetch_method="bash_curl".
    - optional query parameters cause empty results on a known JSON endpoint -> retry same endpoint without optional filters, then persist the simpler endpoint only if it returns parseable jobs.
    - configured slug 404s but a verified discovery action provides a same-company first-party URL -> infer the new slug/provider and probe once.

  For every repair attempt, write a run-log entry in `connector_repairs`.
  If repair succeeds: update companies.json, reset ats_error_consecutive_days to 0, and append a compact ats_repair_history entry.
  If repair fails or is unsafe: leave config unchanged, increment ats_error_consecutive_days, mark the company ATS-incomplete for Indeed fallback, and create or update a DISCOVERY-ACTIONS.json action with source_signal="ats_error".

Priority: within each ATS provider, process verified discovery actions first, then companies with same-day/fresh urgent LinkedIn stubs, then continue the normal company order. This changes order only; it does not bypass search_mode, hard filters, dedupe, or scoring.

companies.json ATS configuration examples, based on known working provider patterns:

```json
[
  {
    "name": "Greenhouse Example",
    "indeed_keywords": ["Greenhouse Example Product Manager"],
    "ats": [
      {
        "provider": "greenhouse",
        "slug": "greenhouse-board-slug"
      }
    ],
    "note": "Uses https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
  },
  {
    "name": "Ashby Example",
    "indeed_keywords": ["Ashby Example Product Manager"],
    "ats": [
      {
        "provider": "ashby",
        "slug": "ashby-board-slug"
      }
    ],
    "note": "Uses https://api.ashbyhq.com/posting-api/job-board/{slug}. Do not append includeCompensation=true; some tenants reject it."
  },
  {
    "name": "Lever Example",
    "indeed_keywords": ["Lever Example Product Manager"],
    "ats": [
      {
        "provider": "lever",
        "slug": "lever-company-slug"
      }
    ],
    "note": "Uses https://api.lever.co/v0/postings/{slug}?mode=json"
  },
  {
    "name": "iCIMS JSON API Example",
    "indeed_keywords": ["iCIMS JSON Example Product Manager"],
    "ats": [
      {
        "provider": "icims",
        "endpoint": "https://careers.example.com/api/jobs?page={page}&limit=100",
        "type": "json_api",
        "fetch_method": "bash_curl"
      }
    ],
    "note": "Large iCIMS-style JSON API. Full JDs are already in the API response; no drill-in needed. Use bash_curl if web_fetch truncates large JSON."
  },
  {
    "name": "iCIMS HTML Category Example",
    "indeed_keywords": [],
    "indeed_broken": true,
    "ats": [
      {
        "provider": "icims",
        "endpoint": "https://careers.example.com/search-jobs?category-filter=PRODUCT_MANAGEMENT",
        "type": "html_category",
        "fetch_method": "web_fetch",
        "drill_in_base": "https://careers.example.com"
      }
    ],
    "note": "iCIMS-style HTML category page. Parse list-page job links, then drill into each job page for full JD."
  }
]
```

### Workday (one company per bash invocation, curl only)

RULES:
• ONE company per bash invocation
• Use the Workday CXS POST endpoint: `https://{host}/wday/cxs/{tenant}/{site}/jobs`
• Use `limit=20`; larger limits can return HTTP 400 on some tenants.
• Use bounded offset pagination for Workday instead of accepting offset=0 truncation:
  - Fetch offset 0 first for every searchText.
  - If offset 0 reports total > 20, also fetch offsets 20 and 40.
  - For priority tenants or target-lane companies with severe truncation signals, continue through offset 100 while unique PM-title roles keep appearing.
  - Stop pagination for that searchText after two consecutive pages with zero new PM-title roles, an HTTP/parse error, or offset > 100.
  - Never assume offset ordering is newest-first or best-fit; apply title/date/domain scoring after extraction.
• Cache-Control: no-cache, no-store and Pragma: no-cache headers on every call
• curl subprocess only (not Python urllib)
• Run Workday BEFORE Greenhouse (avoids proxy saturation)
• Do not assume any Workday offset is newest or best-fit. Treat pages as search-result samples unless the response itself proves sort/date semantics.
• Do not add an `appliedFacets` date filter unless that exact tenant's CXS response exposes a valid posted-date facet and a probe proves it reduces results without dropping known fresh PM roles. If unproven, prefer targeted `searchText` variants over guessed facet names.
• If a verified discovery action contains an exact Workday listing URL or req ID, run an exact `searchText` query for the visible title and/or req ID before broad variants. If found, score that exact role even if it would not appear in broad offset pages.

```python
import subprocess, json, re

WORKDAY_SEARCH_TEXT_VARIANTS_FROM_CONFIG = CONFIGURED_WORKDAY_SEARCH_VARIANTS_OR_DEFAULT

def wd_fetch(host, tenant, site, search_text, offset=0):
    url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    body = json.dumps({"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": search_text})
    r = subprocess.run(
        ["curl", "-s", "--max-time", "30", "-X", "POST",
         "-H", "Content-Type: application/json",
         "-H", "Accept: application/json",
         "-H", "Cache-Control: no-cache, no-store",
         "-H", "Pragma: no-cache",
         "-d", body, url],
        capture_output=True, text=True
    )
    try: return json.loads(r.stdout)
    except: return {"error": "parse_failed", "raw": r.stdout[:200]}

SEARCH_TEXT_VARIANTS = WORKDAY_SEARCH_TEXT_VARIANTS_FROM_CONFIG
search_variants = SEARCH_TEXT_VARIANTS or [
    "Product Manager",
    "Senior Product Manager",
    "Principal Product Manager",
    "AI Product Manager",
    # Add target-lane variants here, e.g. "{Target Lane} Product Manager"
]
seen = set()
empty_count = 0
total_reported = 0
for search_text in search_variants:
    offsets = [0]
    zero_new_pages = 0
    page_index = 0
    while offsets:
        offset = offsets.pop(0)
        data = wd_fetch(HOST, TENANT, SITE, search_text, offset)
        if "error" in data:
            print("ERROR:" + search_text + ":offset_" + str(offset) + ":" + data["error"])
            break
        postings = data.get("jobPostings", [])
        if offset == 0 and data.get("total", 0) == 0 and not postings:
            empty_count += 1
            break
        if offset == 0:
            total_reported = max(total_reported, data.get("total", 0))
        new_this_page = 0
        for j in postings:
            t = j["title"].lower(); pm = "product manager" in t
            if not pm: continue
            path = j.get("externalPath", "")
            m = re.search(r"_([A-Za-z0-9]+)(?:-\d+)?$", path)
            jid = m.group(1) if m else path
            if jid in seen: continue
            seen.add(jid); new_this_page += 1
            posted = j.get("postedOn", "")
            print(j["title"] + "|" + j.get("locationsText","") + "|" + posted
                  + "|workday:" + TENANT + ":" + jid + "|https://" + HOST + path)
        zero_new_pages = zero_new_pages + 1 if new_this_page == 0 else 0
        next_offset = offset + 20
        severe_truncation = (data.get("total", 0) or 0) > 100
        max_offset = 100 if severe_truncation else 40
        if len(postings) == 20 and next_offset <= max_offset and zero_new_pages < 2:
            offsets.append(next_offset)
if empty_count == len(search_variants) and not seen:
    print("EMPTY_OR_CACHE:total=0")
```

Error handling per company:
  - "ERROR:parse_failed" or HTTP error → log "ats_error:workday:{tenant}", skip company
  - "EMPTY_OR_CACHE:total=0" → log "workday_cache_or_empty:{tenant}", skip (don't retry)
  - "Posted Over 30 Days Ago" in posted field → drop that posting
  - Curl timeout (30s) → log "ats_timeout:workday:{tenant}", skip

If total_reported > len(seen) and total_reported remains much larger than visible PM-title roles after bounded pagination, log `workday_partial_coverage:{tenant}:showing_{len(seen)}_unique_pm_of_{total_reported}` in errors.
Do not log the old `workday_truncated` wording when bounded offset pagination was attempted; use `workday_partial_coverage` so downstream scouts know coverage improved but is still not exhaustive.
This is a known Workday limitation. CXS POST plus bounded offsets materially improves coverage versus one offset-0 query, but large tenants may still be partially sampled.

For each Workday company, log `workday_variant_stats` in the run log with per-variant offsets fetched, returned count, unique_new count, total_reported, and whether pagination stopped due to max_offset or two zero-new pages. If a variant consistently produces 0 unique_new roles across several runs, consider dropping it from the private deployment.

Write checkpoint after all Workday tenants done.

### Greenhouse / Ashby / Lever

Use endpoint templates from companies.json's top-level `ats_endpoints` object when present.
Fallback endpoint templates are:
  - Greenhouse: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
  - Ashby: https://api.ashbyhq.com/posting-api/job-board/{slug}
  - Lever: https://api.lever.co/v0/postings/{slug}?mode=json

Use this bash pattern for every ATS GET fetch:

  HTTP=$(curl -s -o /tmp/ats_response.json -w "%{http_code}" --max-time 30 "{ENDPOINT_URL}")

Error handling per slug:
  HTTP 200 → run extraction script (see below)
  HTTP 404 on CONFIGURED slug (in company's ats[] array):
    → Log "ats_404_configured:{provider}:{slug}" in errors
    → Set company.ats_broken=true, company.ats_broken_since=TODAY in companies.json (if not already set)
    → This company MUST get Indeed coverage — do NOT add to slug_invalid_history
  HTTP 404 on discovery-probe slug:
    → Add to slug_invalid_history with verified_on=TODAY, source="discovery_probe"
  HTTP 429:
    → Sleep 15s, retry ONCE. If still 429: log "ats_ratelimit:{provider}:{slug}", skip.
  Other non-200:
    → Log "ats_error:{provider}:{slug}:HTTP{status}", skip.
  Curl timeout:
    → Log "ats_timeout:{provider}:{slug}", skip.

Before fetching any slug, check slug_invalid_history. Skip if found AND verified_on is within 30 days.

Greenhouse extraction (after HTTP 200):
  python3 -c "
  import json, re
  d = json.load(open('/tmp/ats_response.json'))
  for j in d.get('jobs', []):
      t = j['title'].lower()
      if 'product manager' not in t: continue
      loc = j.get('location', {}).get('name', '')
      date = j.get('updated_at', j.get('first_published_at', ''))[:10]
      cid = 'greenhouse:{SLUG}:' + str(j['id'])
      url = j.get('absolute_url', '')
      comp = ''
      for m in (j.get('metadata') or []):
          if re.search(r'pay|salary|comp', m.get('name',''), re.I): comp = str(m.get('value',''))
      if not comp:
          m2 = re.search(r'\\\$[\d,]+\s*[-–]\s*\\\$[\d,]+', j.get('content',''))
          if m2: comp = m2.group()
      print(j['title']+'|'+loc+'|'+date+'|'+comp+'|'+cid+'|'+url)
  "

Ashby: response key is 'jobs' (not 'jobPostings'). Date from publishedAt. Listing URL: jobUrl → public Ashby job page. Apply URL: applyUrl → applicationUrl.
Lever: date from createdAt (epoch ms ÷ 1000). Comp from salaryRange object.

### iCIMS and other custom endpoints

iCIMS has no standard public API. Each company has a bespoke endpoint discovered via network inspection.
Follow the company-specific fetch method in companies.json. Do not generalize across tenants.

**Large JSON API pattern**:
  Use bash curl and local Python parsing when web_fetch truncates, strips, or over-loads large JSON.
  Example endpoint: https://careers.example.com/api/jobs?page={N}&limit=100
  IMPORTANT: optional filters such as keywords/internal flags can cause empty responses on some tenants.
  Fetch jobs and filter titles client-side unless the endpoint is known to support server-side filtering.
  Response: { jobs: [{data: {title, description, city, state, posted_date, req_id, apply_url, tags2, tags3, ...}}], totalCount: N }
  Extraction (run in bash on the saved JSON):
  ```
  For each job in response.jobs:
    t = job.data.title (lowercase for filter)
    Title pre-filter: must contain "product manager"
    loc = job.data.city + ", " + job.data.state
    date = job.data.posted_date (format: "YYYY-MM-DD")
    comp = job.data.tags2 + " – " + job.data.tags3 (base salary range, e.g. "USD $135,450.00/Yr.")
         fallback: search job.data.description for $NNN,NNN pattern
    cid = "icims:{company_slug}:" + job.data.req_id
    url = job.data.apply_url OR configured career URL template + job.data.req_id
    description = job.data.description (FULL JD — already in the API response)
  ```
  Store description text during extraction when available in the API response; no drill-in is needed if the response already contains the full JD.

**HTML category page + per-job drill-in**:
  Step 1 — list page:
    web_fetch(configured category/search URL from companies.json)
    Response may be SSR HTML. Parse job links matching the site's job URL pattern.
    Extract from each link: title (link text), city (from URL path), full URL.
    Title pre-filter: must contain "product manager".

  Step 2 — drill-in (per surviving job, budget permitting):
    web_fetch(configured drill-in base URL + job path)
    Parse HTML meta tags and body:
      - meta name="meta-dimension19" → posted date (format: "M/DD/YYYY", convert to YYYY-MM-DD)
      - meta name="meta-dimension7" → location ("City~State~Country")
      - meta name="meta-search-job-apply-url" → apply URL
      - meta name="meta-job-ats-req-id" → req ID
      - Comp: search for salary pattern $NNN,NNN in page text
      - cid = "icims:{company_slug}:" + req_id
      - JD text: extract from the job description sections in the HTML body.
        Use bash to parse: pipe web_fetch result through python/sed to extract text between
        job-description markers. Store full JD for lead file.

  Error handling:
    fetch timeout or error → log "ats_error:icims:{company}", mark ATS-incomplete, and let Indeed provide fallback coverage.
    Empty/malformed response → log "icims_empty:{company}", skip.
    Large unsorted feed sampled with no matching titles → log "icims_search_exhausted:{company}" and mark ATS-incomplete, not ATS-complete.

**Custom public HTML listing + per-job drill-in**:
  Use only for a company entry explicitly configured with `provider="custom"`, `type="html_listing"`, and `job_path_prefix`.

  Step 1 — fetch the configured first-party listing page once. Parse only anchor URLs whose normalized path starts with `job_path_prefix`; deduplicate by normalized path. Do not crawl other site links.

  Step 2 — title-filter the anchor text for the rubric title gate. Fetch only surviving public detail pages.

  Step 3 — use the public detail page as `listing_url` and extract its visible JD text. Create a stable canonical ID as `custom:{company_slug}:{detail_page_slug}`. Treat the embedded first-party form or page's public Apply control as the apply path; do not submit it.

  Date boundary: a custom page with no stated posted date is not automatically fresh merely because this scout found it today. Score it only when a same-day/yesterday email or other fresh signal corroborates it; otherwise log `custom_html_unknown_date:{company}:{title}` and leave it for manual resolution rather than creating an active lead.

  Error handling: listing-page or detail-page fetch error → log `ats_error:custom:{company}`, mark ATS-incomplete, and let Indeed provide fallback coverage. Unknown page structure or no matching paths is a clean zero-result, not a reason to crawl more broadly.

Write checkpoint after all ATS passes done.

================================================================
HARD FILTERS — apply to every candidate before scoring

Apply the hard filters from rubric.md Step 2:
  (H) Title: must pass rubric.md Step 1 title gate (already enforced in bash, double-check)
  (A) Dedupe: drop if source_id/canonical_id/canonical_key is already in seen_job_ids OR this run's already-processed list OR role-ledger exact/apply-URL duplicate. For role-ledger probable cross-source duplicates, refresh the existing lead file/ledger instead of creating a second active lead file.
  (B) Date: drop if posted > 7 days before TODAY. Unparseable → keep.
  (C) Comp: apply the private compensation rule in rubric.md. Keep absent or unparseable compensation as unverified.
  (D) Location: per rubric.md location rules. Null → keep.
  (E) Title blacklist: per rubric.md
  (F) Company exclusions: per rubric.md
  (G) People-management: per rubric.md (current requirement = drop; future/optional = keep)

================================================================
SCORING

Before scoring, sort surviving candidates so exact or near matches to urgent LinkedIn stubs (same company plus overlapping title terms) are first, then all other candidates.

For each candidate surviving hard filters:
  1. Fetch the full job description (drill-in) if not already in the extraction output.
     For Greenhouse: content is in the initial fetch (content=true param).
     For Workday: fetch the individual job page via curl.
     For Ashby/Lever: description is in the initial fetch.
     For iCIMS/custom JSON APIs: description may be in the initial API response.
     For iCIMS/custom HTML pages: description is fetched during per-job drill-in.
  2. Score using rubric.md Step 3. Produce: score, freshness bucket, match summary, gaps, recommended resume, application priority, decision, and caveat if needed.
  3. Evidence sanity check: before writing a lead file, ensure the match summary and fit claims cite only candidate-profile/resume/evidence facts. Remove or rewrite any claim that treats application targets, interview history, recruiter notes, company research, or lead files as experience.
  4. Do not treat score as the only priority signal. A Same-day or Fresh role with a clean resume path can be more urgent than an older higher-score role.

Workday no-JD placement:
  - If a Workday candidate's full JD cannot be retrieved, treat the score as provisional title-only evidence.
  - Put it in Yes only when it is exact/near-match to a fresh LinkedIn or verified discovery signal, or the title plainly names one of the target lanes defined in candidate-profile.md.
  - If the title is generic, niche outside profile, underlevel, or domain-ambiguous, write the audit file to No even if the provisional score is 50-64. Examples: generic "Product Manager", quantum-specific, physics-specific, creative/marketing/security without direct evidence.
  - If it is high-value but blocked only by Workday rendering, write a visible Manual Check file instead of pretending the title-only score is reliable.

================================================================
URL POLICY — visible links must open readable listings

Every lead file must include a primary `Listing` URL that opens the readable job description page. Do not make the visible primary link an apply/login/session URL.

Use these URL fields:
  - listing_url: first-party readable job page where the user can inspect the JD.
  - apply_url: optional application/login URL, used only as secondary metadata.

Provider rules:
  - Greenhouse: prefer `absolute_url`; otherwise build `https://job-boards.greenhouse.io/{board}/jobs/{id}`. Never use `boards-api.greenhouse.io` as the visible Listing URL.
  - Ashby: prefer `jobUrl`; otherwise build `https://jobs.ashbyhq.com/{board}/{job_id}`. Do not use `applyUrl`, `applicationUrl`, or `/application` as Listing.
  - Lever: use `hostedUrl` or `https://jobs.lever.co/{slug}/{id}` as Listing.
  - Workday: use the public career-site job URL containing `/job/`, not login/session URLs.
  - iCIMS/custom: use the public careers listing/drill-in page as Listing. Do not use `/login` as Listing.
  - Some official career URLs include words like `applications` in readable listing paths. They are valid Listing URLs when they open the public job description without a login/session.
  - Indeed redirects are not listing URLs. If no first-party listing can be resolved, mark the listing unresolved instead of exposing a redirect as Listing.

If listing_url and apply_url differ, include both. If apply_url is a true login/session/apply-form endpoint, write `**Apply:** Apply through listing page` instead of exposing the login URL.

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
**Source:** {ATS provider}:{slug}
**Listing:** {listing_url}
**Apply:** {apply_url_or_"Apply through listing page"}
**Scouted:** {TODAY}

## Why this is a fit
{one sentence citing specific qualification overlaps from rubric evaluation}

## Gaps
- {gap 1}
- {gap 2}
- {gap 3}

## Recommended resume
{{RESUME_VARIANT_1}} / {{RESUME_VARIANT_2}} / {{RESUME_VARIANT_3}} — whichever of {{CANDIDATE_FIRST_NAME}}'s configured resume variants best fits this role

## Application priority
{Apply / Review / Park / Skip}

## Caveat
{optional caveat from rubric; omit section if none}

## Full job description
{Full unabridged JD text in readable Markdown/text. Preserve all substantive sections from the fetched posting so the user can read the role later without reopening the web page. Do not summarize or paraphrase.}
---

If description_text is null (failed to fetch): still write the lead file but note "JD not retrieved — apply link above" in place of the description. Do NOT skip the lead file.

================================================================
DAILY-BRIEF.md

Do not write DAILY-BRIEF.md. Lead files are the human source of truth. Run logs, ATS state, ACTION-REQUIRED.md, seen-jobs.json, role-ledger.json, and DISCOVERY-ACTIONS.json are machine-readable infrastructure. Avoid duplicating action items or status summaries across hidden files.

================================================================
ACTION-REQUIRED.md — append only (do not overwrite existing entries)

Path: {{JOB_SCOUT_DIR}}/ACTION-REQUIRED.md
Append `### {YYYY-MM-DD} — {description}` + details + `Status: OPEN` only for: unrepaired ATS 404 on configured slug, company with no ATS + no Indeed results for 14+ days, or the same connector error persisting for 3+ completed runs. Skip if an identical open entry exists. Do not add Workday truncation by itself; it belongs in the run log and ATS state unless it blocks a specific high-priority lead.

================================================================
STATE UPDATE (after lead files written)

1. Append scored candidates' canonical_keys to seen_job_ids in seen-jobs.json.
   Do NOT add unscored/error-blocked candidates to seen_job_ids.
2. Update role-ledger.json for every scored, refreshed, suppressed duplicate, and distinct same-title candidate:
   - new non-duplicate role -> append ledger entry with role_key, display title/company, current_folder, lead_file_path, score, priority, source_ids, listing_urls, apply_urls, first_seen, last_seen
   - duplicate/refresh -> update existing source_ids/listing_urls/apply_urls/last_seen/latest_seen_score and source history; append `## Scout Refresh` to the existing lead_file_path when useful
   - distinct same-title role -> add role_key_suffix and log why it was kept separate
   Validate JSON after writing. If validation fails, restore prior role-ledger.json and log failure.
3. Write seen-jobs.json.
4. Update companies.json: surface_count/last_surfaced_on for surfaced companies, ats_broken flags, ats_error_consecutive_days, source_status, and any successful connector repairs.
   Discovery source-state rules:
   - For companies added through verified discovery actions, start with source_status="probation".
   - Increment probation_attempts only after an ATS source is actually fetched.
   - Promote source_status to "active" if the company produces any scored lead above the configured surface threshold or repeated title survivors in target lanes.
   - Move source_status to "dormant" and search_mode="dormant" for a private-configured cooldown period if probation_attempts >= 3 and the source produced zero relevant title survivors and zero leads.
   - Move source_status to "manual_watch" when the source is first-party but unsupported, intermittently parseable, or only useful for exact-job verification.
   - Move source_status to "blocked" only after repeated confirmed bad data, persistent irrelevant results, or a source known to poison the run.
   - Do not automatically dormant high-priority curated companies; log them in ACTION-REQUIRED.md if their source repeatedly fails.
   - Keep ats_repair_history compact: last 5 repair entries per company.
5. Update DISCOVERY-ACTIONS.json if loaded:
   - verified actions successfully consumed by ATS → status="consumed", consumed_on=TODAY
   - verified actions that could not be parsed/fetched → status="failed" or "manual_check" with concise reason
   - unresolved connector errors needing source re-resolution → status="open", action="resolve_first_party_source", source_signal="ats_error"
   - unresolved open signals remain unchanged
6. Write final ATS state file for Indeed coordination:
   {{JOB_SCOUT_DIR}}/run-TODAY-ats-state.json
   {
     "run_date": "YYYY-MM-DD",
     "partial": false,
     "last_pass_completed": "done",
     "ats_complete_companies": ["company-a", "company-b", ...],
     "ats_broken_companies": ["company-c", ...],
     "ats_incomplete_companies": ["company-d", ...],
     "new_canonical_ids": [...],
     "workday_truncated": ["company-e", "company-f", ...]
   }
   ats_broken_companies: companies whose configured ATS slug 404'd — Indeed MUST search these.
   ats_incomplete_companies: companies whose ATS exists but did not provide reliable title coverage, such as unsorted large feeds with zero matching titles in sampled pages. Indeed SHOULD search these.
   workday_truncated: company slugs, optionally with detail after a colon, for Workday tenants where title matches exceed visible fetched results. Indeed SHOULD parse the slug before any colon and provide fallback coverage.
7. Write run log: {{JOB_SCOUT_DIR}}/run-TODAY-ats.json
   Include discovery_actions_consumed, discovery_actions_failed/manual_check, discovery_actions_deferred, connector_repairs, companies_auto_repaired, companies_promoted_active, companies_moved_dormant, workday_title_only_to_no, workday_title_only_manual_check, ledger_exact_duplicates, ledger_url_duplicates, ledger_cross_source_refreshes, ledger_same_title_distinct_roles, and role_ledger_updates if applicable.
8. Delete progress checkpoint.
================================================================
RULES

- Retry once on tool/HTTP errors. 429 → sleep 15s, retry once. Never sleep > 15s.
- Curl timeout or bash hang → skip company, log distinctly from empty. Use `timeout 45 curl -s --max-time 30 ...`.
- companies.json or rubric.md unreadable → stop, write run log.
- CRITICAL: on partial completion, STILL write ATS state file + run log with whatever completed. Partial state > absent state (absent wastes Indeed's entire budget).
- ATS 404 on configured slug -> safe retry, set ats_broken/ATS-incomplete as appropriate, create/update a source-resolution action, and ensure Indeed covers it. ACTION-REQUIRED.md is bot-internal diagnostics only.
- Verified discovery action fails → update DISCOVERY-ACTIONS.json with failed/manual_check status; do not silently drop it.
- Never add unscored candidates to seen_job_ids.
- Never silently drop a candidate after full drill-in. Metadata/title/date hard-filter drops may be summarized in the run log; candidates with fetched full JDs must be scored, carried forward, or listed as unscored/error-blocked.
- Hidden logs and queues are not a user interface. If user action is required, write a visible lead file.
- FORBIDDEN: LinkedIn, Glassdoor, ZipRecruiter, web search, browser automation.

================================================================
DEFINITION OF DONE
✓ Lead files/manual-check files, ACTION-REQUIRED (if applicable, bot-internal only), seen-jobs.json, role-ledger.json, companies.json, DISCOVERY-ACTIONS.json if loaded, run-TODAY-ats-state.json, run-TODAY-ats.json all written
✓ No files exist under {{SKILL_SOURCE_DIR}}/leads; all visible leads are in {{LEADS_DIR}} disposition folders
✓ All outputs written to canonical paths; no required state exists only in local-agent outputs
✓ Progress checkpoint deleted
