# Job Scout Bot

LLM-driven job scouting workflow for finding, filtering, scoring, and triaging job leads across:

- LinkedIn and explicitly configured employer job-alert emails
- First-party web/source discovery
- Company ATS pages
- Indeed search and drill-ins

Built for [Claude Cowork](https://claude.ai), Anthropic's desktop tool for automating file and task management. Cowork can read and write local files, connect to external services via MCP connectors, run scheduled tasks, and execute multi-step skill prompts — which is what the files in this repo are.

The workflow is designed around four principles:

1. Speed matters for competitive roles.
2. Aggregators are signals; first-party job listings are the source of truth.
3. Generic qualifications should not inflate fit scores.
4. Aspirational pivot roles should surface for review without competing with true high-fit roles.

## Repository Structure

```text
skills/
  SKILL-linkedin.md     # Job-alert email discovery pass
  SKILL-web-discovery.md # First-party source resolver
  SKILL-ats.md          # ATS sweep pass
  SKILL-indeed.md       # Indeed fallback/search pass

config/
  rubric.template.md
  companies.example.json
  candidate-profile.example.md
  discovery-actions.example.json
  email-alert-sources.example.json
  role-ledger.example.json

docs/
  COMPANIES_SCHEMA.md
  SCORING_EXAMPLES.md
```

Supporting docs:

- `docs/COMPANIES_SCHEMA.md` explains the `companies.json` structure, including real ATS provider patterns for Greenhouse, Ashby, Lever, Workday, and iCIMS.
- `docs/SCORING_EXAMPLES.md` shows how to avoid common scoring mistakes such as over-crediting generic requirements, underweighting preferred qualifications, and confusing bridge roles with domain mismatches.

## Important

Use `config/rubric.template.md` as the starting rubric and customize it for your target function, constraints, and search strategy.

This repository is a prompt/workflow scaffold designed for **Claude Cowork**. It is not currently packaged as a natively supported workflow for other agent runtimes.

The workflow assumes Claude Cowork has:

- read and write local files,
- access email for LinkedIn and configured employer job alerts,
- search the web and fetch public first-party career/ATS pages,
- an Indeed MCP connector for search and job-detail drill-ins,
- schedule recurring runs.

### Sandbox Allowlist

Cowork runs web fetches through a sandboxed environment that blocks outbound requests by default. To allow ATS and career-page fetches, add the required domains to your sandbox allowlist in the Claude desktop app under **Settings → Network** (or the equivalent admin setting for your plan).

Required domains depend on your company list, but commonly include:

```text
*.ashbyhq.com
*.myworkdayjobs.com
api.lever.co
boards-api.greenhouse.io
jobs.lever.co
job-boards.greenhouse.io
careers.example.com
jobs.example.com
```

Add any additional company ATS or career-site domains you configure in `companies.json`.

## Setup

Recommended: use Claude or your preferred coding agent to personalize this repo. The files are intentionally written as editable prompt/config scaffolds, and an agent can update placeholders, align the rubric, adapt the skills to your target function, and keep terminology consistent across files faster than doing it by hand.

Expect to debug the workflow with Claude Cowork as an active partner. Career sites, ATS endpoints, MCP connector names, sandbox allowlists, and search behavior vary by user and change over time. This repo provides a working scaffold, not a no-touch product; your deployment will likely need iterative fixes for your target roles, company list, connectors, and local environment.

### 1. Create Your Working Directory

Create a private working directory outside this public repo. Copy the reusable files into it:

```text
job-scout/
  rubric.md
  candidate-profile.md
  companies.json
  seen-jobs.json
  role-ledger.json
  linkedin-processed.json
  DISCOVERY-ACTIONS.json
  leads/
    Yes/
    WIP/
    No/
    Archived/
```

Suggested starting files:

- Copy `config/rubric.template.md` to `rubric.md`.
- Copy `config/candidate-profile.example.md` to `candidate-profile.md`.
- Copy `config/companies.example.json` to `companies.json`.
- Copy `config/discovery-actions.example.json` to `DISCOVERY-ACTIONS.json`.
- Copy `config/role-ledger.example.json` to `role-ledger.json`.
- Create `seen-jobs.json` with `{"seen_job_ids":[]}`.
- Create `linkedin-processed.json` with `{"processed_message_ids":[],"last_run":null}`.

### 2. Update Candidate Information

Edit `candidate-profile.md` with:

- your target roles,
- relevant background,
- resume variants,
- strengths and gaps,
- location constraints,
- salary expectations,
- work authorization constraints,
- domains to prioritize,
- domains to avoid.

Keep this file private. It will contain personal career strategy.

### 3. Update Search Criteria

Edit `rubric.md` for your search:

- title gate,
- hard filters,
- compensation floor,
- location rules,
- excluded companies or industries,
- scoring weights,
- preferred qualification logic,
- pivot/aspirational-role logic,
- output format.

Use `docs/SCORING_EXAMPLES.md` while customizing the rubric. The examples are generic, but they capture the judgment patterns the bot needs: generic requirements do not prove fit, preferred qualifications can define the real hiring profile, and plausible adjacent roles should be handled differently from random domain mismatches.

The provided examples are product-management oriented. If you are searching for another function, change the rubric and skills accordingly:

- Data science: replace the title gate with data scientist, applied scientist, research scientist, ML scientist, or analytics titles; update scoring around modeling, experimentation, causal inference, production ML, domain expertise, and publication/research expectations.
- Finance: replace the title gate with finance, strategy, FP&A, corporate development, investment, or analyst/manager titles; update scoring around forecasting, budgeting, valuation, accounting, capital allocation, and industry coverage.
- Engineering: replace the title gate with the relevant engineer titles; update scoring around coding depth, architecture, systems, language/framework requirements, and production ownership.

### 4. Update the Skills Themselves

The skill files contain assumptions that may need editing:

- `skills/SKILL-linkedin.md`
  - Gmail query for LinkedIn alerts.
  - Job-title parsing rules.
  - Discovery-priority categories.
  - Urgent-stub criteria.

- `skills/SKILL-web-discovery.md`
  - First-party source verification rules.
  - Search budget and freshness window.
  - Supported ATS/source patterns.
  - Rules for turning signals into ATS actions.

- `skills/SKILL-ats.md`
  - ATS providers to inspect.
  - Title pre-filter.
  - Hard-filter assumptions.
  - Lead-file output format.
  - Resume-variant labels.

- `skills/SKILL-indeed.md`
  - Indeed query strategy.
  - API-call budget.
  - Company-search vs. keyword-search allocation.
  - Keyword sweeps.
  - Drill-in priority rules.

At minimum, replace every `{{...}}` placeholder and review every rule that says `Product Manager`, `PM`, `resume variant`, `domain`, `salary`, or `location`.

### 5. Configure Companies

Edit `companies.json` with companies you want actively searched.

Each company can include:

- display name,
- tier,
- category,
- ATS configuration,
- Indeed keywords,
- search mode,
- notes.

Keep this list focused. Too many low-yield companies will consume search budget and reduce lead quality.

See `docs/COMPANIES_SCHEMA.md` for the expected `companies.json` structure and ATS provider examples.

Companies can move through lifecycle states:

- `signal_only`: seen as a lead source signal, not yet first-party verified.
- `probation`: first-party source verified, but yield is still being tested.
- `active`: verified source with relevant roles or leads.
- `dormant`: temporarily suppressed after repeated zero-yield checks.
- `manual_watch`: useful only for exact-role checks or manual review.
- `blocked`: known bad/noisy source.

### 6. Configure Connectors and Runtime Paths

The skills require MCP connectors for email and job search. Install them from the Cowork connector menu:

- **Gmail connector** — used by the LinkedIn skill to read job alert emails and archive them after processing.
- **Indeed connector** — used by the Indeed skill for `search_jobs` and `get_job_details` calls. Search for "Indeed" in the Cowork connector list and follow the setup flow to connect your account. If your environment does not provide an Indeed connector, replace `skills/SKILL-indeed.md` with an equivalent source-specific search pass.
- **Web search/fetch access** — used by the web-discovery and ATS skills to verify first-party listings and fetch public career-page data.

After connectors are installed, replace the placeholders in the skill files:

- `{{CANDIDATE_NAME}}` / `{{CANDIDATE_FIRST_NAME}}` — your name as used in prompts.
- `{{JOB_SCOUT_DIR}}` — the absolute path to your private runtime/state directory.
- `{{LEADS_DIR}}` — the absolute path where visible lead files should be written. This can be `{{JOB_SCOUT_DIR}}/leads` or a separate job-search folder.
- `{{APPLICATIONS_DIR}}` — the absolute path where applied-job JDs are archived (one subfolder per company).
- `{{SKILL_SOURCE_DIR}}` — the folder containing the copied skill files, if your runtime distinguishes read-only skill content from writable state.
- `{{SESSION_OUTPUTS_DIR}}` — optional placeholder for your agent runtime's temporary output folder. Treat this as quarantine only, not durable state.
- `{{CANDIDATE_PROFILE_PATH}}` — the absolute path to your `candidate-profile.md`.
- `{{CONNECTOR_ID}}` / `{{TOOL_NAME}}` — the MCP connector and tool names exposed by Cowork for email search, email archiving, Indeed search, and Indeed job details. You can find these in Cowork's connector settings or by asking Claude to list available tools.
- `{{RESUME_VARIANT_1}}` / `{{RESUME_VARIANT_2}}` / `{{RESUME_VARIANT_3}}` — labels for your resume variants (must match `candidate-profile.md`).

### 7. Run Order

Each skill file in `skills/` is a standalone prompt that Claude executes as a scheduled task. To set them up, ask Claude in Cowork to create a scheduled task for each skill — for example: "Schedule the LinkedIn discovery skill to run every night at midnight." Claude will read the skill file, create the task, and run it on the configured schedule.

Run the bots in this order:

1. Job-alert email discovery
2. Web discovery/source verification
3. ATS sweep
4. Indeed fallback/search

Schedule them roughly one hour apart. Example:

```text
12:00 AM  LinkedIn discovery
1:00 AM   Web discovery/source verification
2:00 AM   ATS sweep
3:00 AM   Indeed sweep
```

The order matters:

- The email pass extracts weak signals from LinkedIn and explicitly configured employer alerts, then writes one-day urgent stubs. Its private `email-alert-sources.json` allowlist must constrain every Gmail query by sender or the `job-scout-alert` label.
- Web discovery verifies first-party job pages or ATS sources, then writes source-resolution actions before a company becomes a recurring target.
- ATS consumes verified actions, checks configured company career pages, scores first-party jobs, and writes ATS state.
- Indeed uses ATS state to avoid duplicate work, scores fallback candidates, and writes source-resolution actions for promising new companies.

Downstream scouts should check for a newer completed upstream log before running. Do this by comparing file modification order, not calendar dates or a 24-hour window, because scheduled runs often cross midnight. Same-day manual reruns should still be allowed when explicitly requested.

The skill source folder should be treated as read-only instructions. Runtime files and generated leads should be written only to `{{JOB_SCOUT_DIR}}` and `{{LEADS_DIR}}`; session-output folders are quarantine/fallback only and should not become the source of truth.

### 8. Review Outputs

Primary outputs:

- `leads/{Yes,WIP,No,Archived}/*.md`: scored lead files with full job descriptions. `Yes` is the active review queue; `Archived` holds stale, duplicate, expired, applied, or historical files. Applied-job JDs should be copied into your interview-prep JD archive before the original lead is archived.
- `run-YYYY-MM-DD-linkedin.json`: LinkedIn discovery run log.
- `run-YYYY-MM-DD-web-discovery.json`: first-party source-resolution run log.
- `run-YYYY-MM-DD-ats.json`: ATS run log.
- `run-YYYY-MM-DD-indeed.json`: Indeed run log.
- `DISCOVERY-ACTIONS.json`: queue of source-resolution and verified ATS actions.
- `role-ledger.json`: cross-source duplicate ledger for the same real-world role.
- `ACTION-REQUIRED.md`: only for setup or system diagnostics. Human job actions should also appear as visible lead files.
- `URGENT-LINKEDIN-LEADS.md`: one-day lightweight stubs from LinkedIn and configured employer alert emails; the legacy filename is retained for compatibility.

Lead files are the human-facing workflow. Run logs, queues, and ledgers are machine-readable infrastructure. If a bot finds something that requires user action, it should create or update a visible lead file instead of hiding the action only in a log.

## What Was Excluded

The live operational files are not in this repo:

- private candidate profiles
- private rubrics
- private company lists
- run logs
- progress checkpoints
- seen-job state
- role-ledger state
- discovery-action queue
- LinkedIn processed-message state
- daily briefs/action files
- generated lead files
- backup files
- `.DS_Store`

Those files contain personal search history, job-application strategy, inferred preferences, and potentially email-derived data.

### Publishing Safety Check

Treat this repository as a reusable scaffold, not as the runtime. Keep personal background, resumes, compensation rules, target/avoid lanes, employer-alert senders, company lists, generated leads, and application history in the private runtime directory.

`.gitignore` prevents newly created private runtime files from being added accidentally; it cannot remove files that are already tracked. Before publishing, inspect the staged diff and confirm that only generic `*.example.*`, templates, documentation, and skills are included.
