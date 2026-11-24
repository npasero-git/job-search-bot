# Job Scout

An agent-assisted job search: email alerts → web discovery → company job boards → optional Indeed. Produces scored leads with full job descriptions and visible uncertainties. Never applies or contacts employers for you.

## Start Here

1. Download and extract the repository ZIP, or clone it. You can start from Downloads.
2. Open it in an agent with local file access and web tools, such as Codex or Claude Cowork. Python3.10+ is required. An ordinary chat without file access cannot complete setup.
3. Paste this prompt:

> Read AGENTS.md, then walk me through docs/WELCOME.md. Keep it brief and help me customize the starting rubric. Set up a permanent folder on my computer, validate access, give me LinkedIn searches and alert instructions, and show me an example before live searches. Ask before scheduling tasks or archiving email.

**Start with the wizard; no manual configuration is needed beforehand.** The agent gathers your answers and creates the configuration. You authorize service connections, enable LinkedIn alerts, review a small trial run, and then approve scheduling.

Downloads is the starting package, not the permanent workspace. Choose a folder such as `Documents/Employment/Job Scout`; the agent must verify access there rather than silently using an app-owned or temporary folder.

Indeed is optional and supported only through Claude's search/full-job-detail connector in this release. The ChatGPT Indeed app isn't a supported replacement; use bots1–3 in ChatGPT/Codex where their tools are available.

For manual setup, follow [the wizard](docs/WELCOME.md):

```sh
python3 scripts/setup.py init --workspace /absolute/private/job-scout
# Complete Instructions/settings.json in that private workspace.
python3 scripts/setup.py validate --workspace /absolute/private/job-scout
```

## Run And Review

Run **1. Email → 2. Discovery → 3. ATS → 4. Indeed, if enabled**, sequentially or on suitably spaced schedules. Gates prevent overlap; they don't queue skipped runs. A due daily ATS sweep can run independently after upstream failure. Setup creates no schedules.

Review the private `Leads/Yes` queue. Keep resumes, pay requirements, profile answers and runtime files outside this public checkout. Scores prioritize review; they aren't hiring predictions.

Details: [onboarding](docs/WELCOME.md) · [rubric](config/rubric.template.md) · [workflow, upgrades and tests](docs/WORKFLOW.md) · [company sources](docs/COMPANIES_SCHEMA.md).
