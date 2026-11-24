# Workflow Contracts

## Shared Behavior

Email writes signals, discovery verifies sources, ATS scores first-party jobs, and optional Indeed supplies fallback. All stages share one lock and durable paths. A blocked stage does not claim it ran; a due ATS sweep can work independently of a stalled signal stage. Catch-up runs should be sequential.

The public prompts preserve first-party verification, source-bound evidence, bounded Workday variants, custom-source contracts, exact-ID deduplication, publication precedence, unknown-date manual checks, broad retrieval before location decisions, compact score calculations, existing caps, technical repair and partial coverage reporting.

Configuration replaces personal evidence, titles, geography, compensation, domain priorities, resume labels, company rankings, inbox queries and permissions. These differences are intentional. No retired dedicated pivot bot, personal application workflow, cloud transport or production schedules are installed.

## Runtime Files

- companies.json: public source configuration plus private user selection and local source history.
- URGENT-LINKEDIN-LEADS.md / linkedin-processed.json: signals and parsed message IDs; never scored-job identities.
- DISCOVERY-ACTIONS.json: version1/actions with stable ID, action/status/target_skill, source evidence, dates, attempts and notes.
- seen-jobs.json: seen_job_ids for scored exact identities.
- role-ledger.json: version1/roles, source_ids/listing_urls, product/req identity, first_seen/last_seen, score/priority, disposition and lead_file_path.
- run-YYYY-MM-DD-STAGE.json: status, gate evidence, actual work, errors, outputs and relevant score/coverage details.
- run-YYYY-MM-DD-ats-state.json: complete/broken/incomplete/truncated company sets and partial status for fallback.
- run-YYYY-MM-DD-ats-progress.json: run identity, pass, partial candidates and evidence for resumption.

Action states are open/retry/verified/manual_check/consumed/ignored/failed/expired. ATS consumes only unexpired verified add_ats_source or verify_exact_job actions targeted to ATS. Each consumed source must exist in ats after readback. Historical replacements/retirements explain old actions without restoring dead connections.

## Persistence And Failure

Hold the lock across read/decision/write. Save source evidence and lead before marking its identity processed. Read back persisted files before email archiving. Preserve same-day receipts. A partial write is recoverable work, not a successful run; on resumption reconcile the saved lead/identity before repeating writes. Never recreate applied or archived roles based solely on a missing old path.

Source failures go to existing repair actions. A repair may change only a deterministic first-party fetch configuration after verification, preserving old config and history. It cannot change scoring, company priority, exclusions or budgets. Do not count failed retrieval as a zero-yield probation attempt.

## Verification Limits

Offline tests cover setup, lock ownership, arithmetic, source identity, bounded pagination, publication handling and synthetic persistence. They do not test live email mutation, every current career endpoint, unattended scheduling or model interpretation accuracy. Source notes are contracts to verify, not guarantees of current availability.
