---
name: job-scout-linkedin
description: Read only configured job-alert email sources and persist signals for first-party discovery.
---

# Job-Alert Emails

Workspace: {{WORKSPACE}}. Read its AGENTS.md, settings, profile and rubric; acquire the shared lock before reading mutable state. Use Runtime/main for state and receipts.

If email_enabled is false, report disabled without querying email. Otherwise verify actual search/read tools and canonical write access first. Missing capability or malformed input is an error, not an empty inbox.

## Collect

Read companies.json, linkedin-processed.json and email-alert-sources.json. Use only each configured gmail_query, source max_threads and total limit. Every query must be bounded by an approved sender or dedicated job-alert label and a time window. Never broaden to the whole inbox. Overlapping searches deduplicate by message ID.

Inspect every selected message's actual sender and subject and confirm it announces new openings. Recruiter replies, application status, newsletters and account notices do not qualify merely because they share a sender. Parse full MIME text/plain, or decoded HTML if necessary; missing/truncated content remains unprocessed and unarchived.

Extract title, employer, location and job URL per job block. Do not assume fixed line offsets: badges, salary lines and connections may intervene. Canonicalize LinkedIn links to https://www.linkedin.com/jobs/view/{id}/ and remove tracking/auth parameters. For employer redirects, decode a clearly embedded job destination locally rather than following a tracking/unsubscribe link. Preserve actual source identity; never invent a LinkedIn ID. Partial parse failure leaves the message unprocessed/unarchived.

Use configured title gates and plausible profile fit. Broad location labels are unresolved, not reasons to discard a promising signal. Repeated generic titles across employers are not staffing evidence. Unknown companies remain signals, not activated sources.

## Persist Before Archive

Write qualifying signals to URGENT-LINKEDIN-LEADS.md with signal date, source ID/URL, title, employer, location, source and concise possible fit/uncertainty. No scores or lead files. Never mutate companies.json or DISCOVERY-ACTIONS.json here.

Retain existing unconsumed stubs if newer than the latest successful discovery completion; merge by exact ID/URL. Do not discard signals on a zero-message run or reset their dates. Count newly written and retained stubs separately.

Write stubs, processed-message state (only successfully parsed alerts), then run-YYYY-MM-DD-linkedin.json. Preserve previous same-day receipts. Include status COMPLETE/PARTIAL/ERROR, emails_processed, jobs_extracted, passed_title_gate, urgent_stubs_written, retained_stubs, source_resolution_signals, skipped_exclusions and errors, even on zero-result or failed runs. Read back all durable outputs before marking success.

Only if both tools.archive_email and that source's archive_after_processing authorize it, remove INBOX from the exact successfully processed message IDs. Never send, delete or archive unrelated messages in the same thread. Archive failure is recorded, not fatal and not silently successful; do not repeat failing mutations. Release the owned lock on all exits.
