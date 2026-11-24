---
name: job-scout-indeed
description: Optional Claude-only Indeed connector fallback for this release, with shared evidence and persistence rules.
---

# Indeed Fallback

Supported setup for this release: Claude with its authenticated Indeed connector. ChatGPT/Codex is not a supported Bot 4 automation path; leave indeed_enabled=false there. A ChatGPT Indeed search app is not a drop-in replacement for the connector's search plus full-job-detail workflow. Bots 1-3 remain usable without this stage. Future support requires a separately verified integration, not a changed documentation claim or app installation alone.

Workspace: {{WORKSPACE}}. Read AGENTS.md, settings, profile and rubric; acquire the shared lock before mutable state. If indeed_enabled is false, report disabled. If enabled, discover and verify actual authenticated search and full-job-detail tools. An app mention or installation alone does not prove scheduled availability. Missing tools: report INDEED_UNAVAILABLE, do not fabricate zero leads or substitute web search.

Run after a newer completed ATS receipt, an explicit request, or a valid incomplete Indeed checkpoint. If upstream has not advanced, stop without duplicate work. Read ATS state, companies, urgent stubs, queue, seen-job and role-ledger; malformed JSON is an error.

Build fallback companies by subtracting only truly covered ATS companies: remove broken/incomplete/truncated companies from the skip set, mapping tenant/name and stripping colon details. Partial state says nothing about unlisted providers. Respect inactive and paused/dormant/blocked/signal_only companies and configured user exclusions. Prioritize fresh exact alerts and broken/incomplete sources, then other relevant configured companies and bounded profile-driven discovery.

Stay within budgets.indeed_calls including retries and detail calls; reserve capacity for full JDs rather than spending it all on search results. Search titles/geography from settings, not inherited personal preferences. Apply the shared rubric and exact/cross-source duplicate rules from SKILL-ats.md. No scores from snippets; inspect complete JD, actual work options, pay and publication date. Use score_breakdown and arithmetic validation, preserving all actual alternatives and gaps.

Known-company full JDs may be evaluated from authenticated Indeed details with source labeled honestly. New companies require first-party source verification before recurring activation: append resolve_first_party_source/open actions for discovery, not direct companies.json additions. Keep source IDs stable; never relabel Indeed IDs as ATS IDs.

Prefer readable first-party/Indeed listing URLs. If only a redirect/apply URL is available, mark Listing unresolved and preserve it as Source URL, not a readable listing. Strong unscored access checks stay visible; weak/known-stale/duplicate jobs do not create user work.

Persist leads, ledger/seen state and discovery actions before run-YYYY-MM-DD-indeed.json. Record call counts, fallback selection, scored candidates/breakdowns, duplicates, unresolved actions and tool/source errors; preserve same-day receipts and validate readback. Unscored/error-blocked jobs are not added to seen-job state. No email, employer contact, application submission, cloud restart or schedule change. Release the lock on every exit.
