# Job Scout

A personal job-search workflow: email alerts -> first-party discovery -> ATS retrieval and scoring -> optional Indeed fallback. It produces readable leads with full job descriptions, evidence-backed fit assessments and visible unresolved questions.

This is an agent-operated workflow, not a standalone search service. Your agent needs local file access, public web retrieval and, optionally, connected email and Indeed tools. Tool availability and scheduling vary by harness; an installed app alone does not establish unattended access. Setup installs no cloud service, paid API or recurring task.

## Start Here

Ask your agent:

> Walk me through docs/WELCOME.md. Explain consequential tradeoffs and let me leave answers unknown. Create my private settings outside this repository, initialize the workspace, validate it, and show me a synthetic lead before running live searches. Do not schedule tasks or archive email without my approval.

Or follow [the welcome wizard](docs/WELCOME.md) yourself. With Python 3.10+:

```sh
python3 scripts/setup.py init --workspace /absolute/private/job-scout
# Complete Instructions/settings.json in that private workspace.
python3 scripts/setup.py validate --workspace /absolute/private/job-scout
python3 -m unittest discover -s tests -v
```

Initialization refuses an existing destination and creates no schedules or network calls. Validation blocks unfilled required values. Unknown geography or compensation stays visible as uncertainty, not guessed eligibility.

## Run And Review

After reviewing the private profile and settings, ask the agent to run the corresponding file in `Instructions/`:

1. `SKILL-linkedin.md`: configured job-alert email sources only; no LinkedIn scraping.
2. `SKILL-web-discovery.md`: verify first-party roles and repair source connections.
3. `SKILL-ats.md`: retrieve configured sources, apply the rubric and write leads.
4. `SKILL-indeed.md`: optional, only when authenticated search/detail tools are actually available.

Run sequentially for an initial or catch-up run. The shared lock prevents overlap; it does not queue blocked stages. Arrange completion-based sequencing where your harness supports it, or separated schedules with explicit skip reporting. Configure schedules only after a supervised run. A due daily ATS sweep may proceed without newer upstream output, without pretending discovery succeeded.

Review `Leads/Yes` for eligible leads and promising unscored checks, `Leads/No` for scored nonmatches, and `Leads/.archive` for historical/duplicate/closed roles. `WIP` is for actual applications underway. Scouts never apply, contact employers, send email or infer submission.

## Included

- Four stage prompts and shared locking/output rules.
- Configurable PM-oriented rubric with explicit alternatives, preferred-evidence accounting and credible transfers.
- Full public company/source starter universe, plus a regional employer seed set. Inclusion is not an endorsement or a fresh endpoint guarantee.
- Bounded Workday retrieval and source-bound caching; custom sources retain extraction contracts.
- Private setup validation and offline synthetic regression/integration tests.

The title examples are PM-oriented. Changing function requires reviewing title filters, provider queries and evidence together, not replacing one word.

## Files

| Repository | Private workspace |
| --- | --- |
| `skills/`, `AGENTS.md` | `Instructions/`, `AGENTS.md` |
| `config/settings.example.json` | `Instructions/settings.json` |
| `config/candidate-profile.example.md` | `Instructions/candidate-profile.md` |
| `config/rubric.template.md` | `Instructions/rubric.md` |
| `config/companies.example.json` | `Runtime/main/companies.json` |
| Empty queue/ledger/email templates | `Runtime/main/` |
| `scripts/ats_fetch.py`, `scripts/scout_io.py` | `tools/` |

See [company contracts](docs/COMPANIES_SCHEMA.md), [scoring examples](docs/SCORING_EXAMPLES.md), and [workflow boundaries](docs/WORKFLOW.md). Tests are developer checks, not steps for scheduled runs.

## Privacy And Limits

Keep the private workspace outside this checkout. Resumes, compensation preferences, profile evidence, correspondence, outcomes, ledgers and receipts must never be committed. The company universe contains public company/source information, not personal rankings or application history. Raw performance reviews are optional private coaching material, not scout inputs.

`.gitignore` is a guard, not a privacy audit. Inspect staged files and history before publishing. Do not paste private files into issues or fixtures. Agent scoring remains judgment: tests establish tested mechanics, not a hiring prediction or exhaustive coverage. Prefer useful matches and reliable handoffs over both exhaustive retrieval and token minimization.
