# Companies Configuration Schema

`companies.json` is the shared state file used by the LinkedIn, web-discovery, ATS, and Indeed passes.

`DISCOVERY-ACTIONS.json` is the separate queue that moves weak signals into first-party verification and then into ATS scoring.

`seen-jobs.json` prevents exact source-ID rescoring. `role-ledger.json` prevents duplicate active lead files when the same real-world role appears through multiple sources or reposts.

The expected top-level structure is:

```json
{
  "version": 2,
  "companies": [],
  "indeed_config": {},
  "slug_invalid_history": [],
  "ats_endpoints": {}
}
```

## companies[]

Each company entry may include:

```json
{
  "name": "Example Company",
  "tier": "1",
  "category": "curated",
  "source": "curated",
  "source_status": "active",
  "indeed_keywords": ["Example Company Product Manager"],
  "ats": [],
  "search_mode": "full",
  "surface_count": 0,
  "last_surfaced_on": null,
  "note": "Optional notes."
}
```

Common fields:

- `name`: Display name.
- `tier`: Candidate-defined company priority, usually `"1"`, `"2"`, or `"3"`.
- `category`: Search category or domain label.
- `source`: Usually `"curated"`, `"web_discovery"`, or `"linkedin_discovery"`.
- `source_status`: Lifecycle state: `"signal_only"`, `"probation"`, `"active"`, `"dormant"`, `"manual_watch"`, or `"blocked"`.
- `indeed_keywords`: Search terms used by the Indeed pass.
- `ats`: ATS provider configuration.
- `search_mode`: `"full"`, `"slug_only"`, `"paused"`, `"dormant"`, `"signal_only"`, `"manual_watch"`, or `"blocked"`.
- `surface_count`: Number of times the company has produced surfaced leads.
- `last_surfaced_on`: Last date a lead was surfaced.
- `note`: Free-form operational note.

Discovery entries may also include:

- `discovery_priority`: `"high"`, `"medium"`, or `"low"`.
- `linkedin_mention_count`: Number of times LinkedIn alerts surfaced the company.
- `added_on`: Discovery date.
- `last_searched_on`: Last date Indeed searched the company.
- `source_status_since`: Date the lifecycle state was set.
- `probation_attempts`: Number of completed fetch attempts for a probation source.

Lifecycle meaning:

- `signal_only`: A company or role appeared in an alert or search result, but no first-party job source has been verified. Do not fetch daily.
- `probation`: A first-party source has been verified, but the bot has not yet proven the source produces relevant roles.
- `active`: Verified source with relevant title survivors or scored leads.
- `dormant`: Temporarily suppressed after repeated zero-yield checks.
- `manual_watch`: Useful only for exact-role checks or manual review.
- `blocked`: Known bad/noisy source.

## ATS Examples

Greenhouse:

```json
{
  "provider": "greenhouse",
  "slug": "greenhouse-board-slug"
}
```

Ashby:

```json
{
  "provider": "ashby",
  "slug": "ashby-board-slug"
}
```

Lever:

```json
{
  "provider": "lever",
  "slug": "lever-company-slug"
}
```

iCIMS JSON API:

```json
{
  "provider": "icims",
  "endpoint": "https://careers.example.com/api/jobs?page={page}&limit=100",
  "type": "json_api",
  "fetch_method": "bash_curl"
}
```

iCIMS HTML category page:

```json
{
  "provider": "icims",
  "endpoint": "https://careers.example.com/search-jobs?category-filter=PRODUCT_MANAGEMENT",
  "type": "html_category",
  "fetch_method": "web_fetch",
  "drill_in_base": "https://careers.example.com"
}
```

Workday:

```json
{
  "provider": "workday",
  "host": "company.wd5.myworkdayjobs.com",
  "tenant": "company",
  "site": "External"
}
```

## indeed_config

Used by the Indeed pass for keyword sweeps.

```json
{
  "pass_2_pm_anchored": {
    "keywords": [
      "Product Manager target-lane-keyword",
      "Product Manager adjacent-lane-keyword"
    ],
    "us_locations": [
      "Target State",
      "Target Metro",
      "Remote"
    ]
  }
}
```

Keep keyword sweeps distinct. Do not fill this with minor variations of the same query.

## DISCOVERY-ACTIONS.json

The discovery-action queue is separate from `companies.json`. The web-discovery pass owns LinkedIn/web/manual source-resolution actions after first-party verification. Indeed may write fallback new-company source-resolution actions from promising search results. The ATS pass consumes verified actions and activates or scores them. LinkedIn writes urgent stubs only; it should not mutate this queue directly.

Expected structure:

```json
{
  "version": 1,
  "last_updated": "YYYY-MM-DD",
  "actions": [
    {
      "id": "stable-short-id",
      "status": "open",
      "action": "resolve_first_party_source",
      "target_skill": "ats",
      "company": "Example Company",
      "title": "Product Manager, Example Domain",
      "location": "Remote",
      "lane": "unknown",
      "priority": "medium",
      "source_signal": "linkedin",
      "source_url": "https://example.com/original-signal",
      "first_party_url": null,
      "ats_provider": "unknown",
      "ats_config": {},
      "evidence": "Aggregator or email signal only; requires first-party verification.",
      "created_on": "YYYY-MM-DD",
      "expires_on": "YYYY-MM-DD",
      "attempt_count": 0,
      "last_attempted_on": null,
      "notes": []
    }
  ]
}
```

Common transitions:

- `open` + `resolve_first_party_source`: weak signal waiting for web-discovery.
- `verified` + `add_ats_source`: first-party ATS source ready for ATS probe/activation.
- `verified` + `verify_exact_job`: exact first-party job URL ready for ATS scoring.
- `consumed`: ATS successfully used the action.
- `manual_check`: first-party source exists but needs human handling.
- `ignored` or `failed`: no useful source or repeated failure.

## role-ledger.json

The role ledger is cross-source duplicate state. It is separate from `seen-jobs.json` because exact source IDs are not enough: one real-world role can appear through an ATS endpoint, a careers page, and an aggregator repost with different IDs.

Expected structure:

```json
{
  "version": 1,
  "last_updated": "YYYY-MM-DD",
  "roles": [
    {
      "role_key": "normalized-company|normalized-title|coarse-location",
      "company": "Example Company",
      "title": "Senior Product Manager, Example Domain",
      "current_folder": "Yes",
      "lead_file_path": "{{LEADS_DIR}}/Yes/82. Example Company - Senior PM.md",
      "score": 82,
      "priority": "Apply",
      "source_ids": ["greenhouse:example:12345"],
      "listing_urls": ["https://job-boards.greenhouse.io/example/jobs/12345"],
      "apply_urls": [],
      "first_seen": "YYYY-MM-DD",
      "last_seen": "YYYY-MM-DD"
    }
  ]
}
```

Use `role_key` for probable duplicates and `source_ids` / URLs for exact duplicates. If two roles share the same generic title but clearly belong to different teams or product surfaces, keep both and add a disambiguating suffix in the ledger entry.

## slug_invalid_history

Used to avoid repeatedly probing known-bad ATS slugs.

```json
{
  "provider": "greenhouse",
  "slug": "old-slug",
  "verified_on": "YYYY-MM-DD",
  "note": "404 on last probe.",
  "source": "discovery_probe"
}
```

## ats_endpoints

Provider endpoint templates used by the ATS pass.

These can stay as provided unless a provider changes its public API.
