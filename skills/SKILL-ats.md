---
name: job-scout-ats
description: Retrieve configured first-party sources, score evidence-backed roles, and persist deduplicated leads and coverage.
---

# ATS Retrieval And Scoring

Workspace: {{WORKSPACE}}. Read AGENTS.md, settings, profile and rubric. Acquire the shared lock, validate canonical input and write access, and load companies.json, DISCOVERY-ACTIONS.json, seen-jobs.json, role-ledger.json and urgent stubs.

## Gate And Recovery

Run when a checkpoint is incomplete, completed discovery is newer than the last completed ATS receipt, an unexpired verified ATS action is pending, the user explicitly requests it, or no completed full sweep exists for today in the configured timezone. Missing upstream output does not block a due daily sweep; record independent mode and the limitation. A completed sweep with source-access errors counts as today's attempt. A gate skip is not a completed sweep.

Resume valid checkpoints instead of restarting. Malformed state is an error, not an empty queue. Preserve prior same-day receipts under .archive/run-receipts. Reuse the current run identity/date, never inherited scratch-script literals. No age-only lock reclamation.

## Verified Actions First

Process unexpired status=verified, target_skill=ats (or legacy absent), action add_ats_source/verify_exact_job before ordinary sweeps. Record one outcome per action: consumed, failed, manual_check, ignored, expired or unprocessed on partial failure.

Probe source adds independently. Persist a working public extraction/pagination/full-JD contract in the company's ats array, read back identity, then consume. Preserve unrelated working connections, exclusions and old configs in compact repair history. Record ats_sources_added with company/provider/connection identity/result/action ID. A note claiming success is not persistence.

Exact jobs can be scored without a full board connection. Strong access-blocked exact jobs use visible manual checks; duplicates are consumed without new active files. Never web-search for guessed sources in this stage.

## Retrieve

Before any sweep/diagnostic fetch, exclude inactive companies/connections. Respect paused/dormant/blocked/signal_only modes; manual_watch is exact-action-only. Expired temporary search modes do not reactivate active=false. Report unattempted sources separately.

Import tools/ats_fetch.py rather than rewriting Workday pagination. Use workday_company, full source_key, save_response/read_response and greenhouse_date. Workday uses six PM query variants (eight for Semiconductor), limit20 and each verified connection's page cap, default1/maximum3. Later-page total=0 does not replace the first total. Duplicates, changed counts, missing pages, malformed rows and capped queries remain incomplete; preserve usable candidates. Query totals include non-PM matches, not an eligible-lead denominator. Never assume first50 is relevance-ranked; do not fetch everything just to make coverage perfect.

Greenhouse: boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true; content contains JD, id is stable, absolute_url is the visible listing. Prefer first_published_at over updated_at, retaining both.
Ashby: api.ashbyhq.com/posting-api/job-board/{slug}; jobs array, publishedAt, jobUrl and descriptionHtml/descriptionPlain.
Lever: api.lever.co/v0/postings/{slug}?mode=json; id, createdAt, hostedUrl and full description/list sections.
Custom/iCIMS: follow that connection's persisted public endpoint, field mapping, pagination and full-JD contract. No universal iCIMS parser. For Qualcomm Eightfold, confirm Product Management filter, paginate data.positions to data.count, verify detail identity and save data.jobDescription; canonical qualcomm:{displayJobId}. See company contracts for Oracle, SuccessFactors and other providers.

Parse large responses locally, returning compact title candidates to the agent. Keep source-bound raw evidence; never relabel another board's cache. Fetch details for surviving jobs before fit decisions. Save full JDs, including qualifications and pay. Reconcile actual requisition body versus stale/blank title/location/pay headers. Reuse same-ID retained first-party evidence for an already resolved sparse-detail case without resetting age.

Apply configured title/function gates locally, then date, compensation, work conditions and actual required management. Do not restrict retrieval to literal city names or turn soft preferences into mandatory filters. Sort fresh exact-alert matches first, then strongest demonstrated domains, then other plausible survivors; ordering is not score inflation.

One retry on transient failures, fifteen-second wait on429, bounded timeout. Respect denied access. Safe repairs require deterministic first-party evidence, parseable jobs, unchanged filters and preserved old config. Otherwise mark incomplete and enqueue one existing-schema source-resolution action. Technical failures do not advance zero-yield probation or establish dormancy. Promote probation from actual relevant yield; respect curated-company exclusions from automatic dormancy.

## Score And Persist

Use rubric.md and settings.weights. Before deductions, check alternatives, depth, required/preferred status and duplicate penalties. Include embedded preferences. Only confirmed absence in a complete JD permits exact required/domain proration; unknown evidence does not. Use the fit-v2 receipt contract (A/B/D/T/S/K, evidence, preferred tally/status, full_jd, weights, proration, cap and unrounded total). Check arithmetic with tools/scout_io.py validated_score(breakdown, settings["weights"]); write_lead reads the same settings. No legacy A+B+C, neutral B15 or generic-domain penalty. Do not replace the calculation with a generic rationale or change historical scores merely because the rubric changed.

Exact source IDs/listing URLs already seen suppress new active files. Only changed full JDs or explicit rescore requests permit a refresh of that record. Check probable cross-source duplicates by product/team/req after detail retrieval; uncertain distinct roles remain visible with a diagnostic, not broad fuzzy suppression. Recheck before write.

Use actual score-prefixed files in Leads/Yes or No under the configured threshold. Genuinely unscored promising checks use Manual Check filenames in Yes; no invented provisional score. Include readable first-party listing, not login/session URLs, full JD and concise user-relevant assessment. Audit details belong in receipts. Never infer application status or modify applications.

Persist leads before seen-job and ledger updates. Never mark unscored/error-blocked candidates seen. Update exact identities, paths, source history and first_seen without resetting age. Write valid JSON atomically/read back, then receipts and ATS state. Update source-repair actions only when recovery is actually verified; retain old failure evidence.

## Coverage And Completion

Checkpoint after provider passes and write partial ATS state even on interruption:
run_date, partial, last_pass_completed, ats_complete_companies, ats_broken_companies, ats_incomplete_companies, new_canonical_ids, workday_truncated.

Keep the downstream contract: complete means provider attempt completed and may overlap incomplete/truncated. Human "fully covered within configured scope" subtracts the union of broken/incomplete/truncated and unfinished providers/failed details, using consistent company identity. Strip colon detail from Workday flags and map tenant to company. Count configured entries separately from provider rows. No claim of whole-company coverage from a department or bounded query.

Write run-YYYY-MM-DD-ats.json with status/gate evidence, action outcomes, source additions/repairs, scored_candidates and score_breakdown, duplicates, manual files, coverage, unattempted sources and errors. Every fetched full JD must have a score, carry-forward or explicit unscored outcome. Read back new files/ledger/receipt and check arithmetic/identity/path consistency before marking done and removing the checkpoint. Keep unresolved work on partial runs. Release only your lock.
