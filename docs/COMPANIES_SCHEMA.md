# Company Sources

companies.example.json is a public starter universe, not a personal target ranking. It retains all main-scout company entries and adds the regional employer seeds. Existing aliases are preserved rather than silently merged. Public extraction contracts are retained; personal annotations, outcomes and run history are removed.

Each entry has name, category, ats, indeed_keywords and search_mode. Semiconductor enables the category-scoped title exception. Other categories start Unclassified for user review; no personal career lanes or ranks are inherited.

An empty ats array is unverified source coverage, not zero vacancies. signal_only entries need discovery before activation. full enables configured sources, manual_watch permits exact-role/manual verification only. Keep active=false on retired connections. No source is guaranteed current.

## Connections

- Greenhouse: provider, slug; preserve case.
- Ashby / Lever: provider, slug.
- Workday: provider, host, tenant, site; optional verified pagination_max_pages, default1/max3.
- Custom / iCIMS: public endpoint or base_url, type, fetch_method, optional drill_in_base/job_path_prefix, and note describing extraction, identity, scope, pagination and full-JD verification.

Custom notes are necessary operational contracts, not arbitrary executable code. Read the relevant connection only; don't load every raw board into model context. Verify IDs/counts and record partial coverage rather than guessing completeness. Inactive or user-excluded sources must not be fetched for diagnostics.

Never place credentials, personal alert IDs or authenticated URLs in public configs. Live source additions belong in the private workspace, after first-party verification. Keep historical source changes in compact private ats_repair_history, not in the public starter.
