---
name: job-scout-linkedin
description: Triage LinkedIn alerts and a bounded general search for recent new-job emails into first-party discovery signals.
---

# Job-Alert Emails

Workspace: {{WORKSPACE}}. Read its AGENTS.md, settings, profile and rubric; acquire the shared lock before reading mutable state. Use Runtime/main for state and receipts.

If email_enabled is false, report disabled without querying email. Otherwise verify actual search/read tools and canonical write access first. Missing capability or malformed input is an error, not an empty inbox.

## Collect

Read companies.json, linkedin-processed.json and email-alert-sources.json. The public starter uses two searches: LinkedIn job alerts, and recent new-opening emails selected by job-alert subject phrases across other senders. Use only the approved gmail_query, source max_threads and total limit; retain the time window. Do not turn the general alert search into an unrestricted inbox search. Overlapping searches deduplicate by message ID.

Review sender/subject/snippet first where the connector exposes them; skip obvious replies, application updates and unrelated mail before fetching bodies. Read bodies only for plausible new-opening alerts. Use the same general job-block extraction for non-LinkedIn messages; no employer-specific sender registry or parser is required. Subject wording can miss some alerts; adjust the small generic phrase set only from observed examples, without building a company-by-company rules catalog.

Inspect every selected message's actual sender and subject and confirm it announces new openings. Recruiter replies, application status, newsletters and account notices do not qualify merely because they share a sender. Parse full MIME text/plain, or decoded HTML if necessary; missing/truncated content remains unprocessed and unarchived.

Extract title, employer, location and job URL per job block. Do not assume fixed line offsets: badges, salary lines and connections may intervene. Canonicalize LinkedIn links to https://www.linkedin.com/jobs/view/{id}/ and remove tracking/auth parameters. For employer redirects, decode a clearly embedded job destination locally rather than following a tracking/unsubscribe link. Preserve actual source identity; never invent a LinkedIn ID. Partial parse failure leaves the message unprocessed/unarchived.

Use configured title gates and plausible profile fit. Broad location labels are unresolved, not reasons to discard a promising signal. Repeated generic titles across employers are not staffing evidence. Unknown companies remain signals, not activated sources.

## Persist Before Archive

Write qualifying signals to URGENT-LINKEDIN-LEADS.md with signal date, source ID/URL, title, employer, location, source and concise possible fit/uncertainty. No scores or lead files. Never mutate companies.json or DISCOVERY-ACTIONS.json here.

Retain existing unconsumed stubs if newer than the latest successful discovery completion; merge by exact ID/URL. Do not discard signals on a zero-message run or reset their dates. Count newly written and retained stubs separately.

Write stubs, processed-message state (only successfully parsed alerts), then run-YYYY-MM-DD-linkedin.json. Preserve previous same-day receipts. Include status COMPLETE/PARTIAL/ERROR, emails_processed, jobs_extracted, passed_title_gate, urgent_stubs_written, retained_stubs, source_resolution_signals, skipped_exclusions and errors, even on zero-result or failed runs. Read back all durable outputs before marking success.

Only if both tools.archive_email and that source's archive_after_processing authorize it, remove INBOX from the exact successfully processed message IDs. Never send, delete or archive unrelated messages in the same thread. Archive failure is recorded, not fatal and not silently successful; do not repeat failing mutations. Release the owned lock on all exits.
