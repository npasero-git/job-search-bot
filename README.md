# Job Scout

Job Scout helps you find openings that fit your experience and what you want next. It reads job-alert emails, searches for opportunities and checks company career pages, then builds a shortlist with full job descriptions, fit assessments and important gaps. You decide which roles to pursue; it never applies or contacts employers for you.

## Start Here

Open **Codex or Claude Cowork** with access to files on your computer, and paste:

> Help me set up Job Scout from https://github.com/npasero-git/job-search-bot. Download the full repository, read AGENTS.md, and guide me through the welcome wizard in docs/WELCOME.md. Ask about my goals, experience and constraints, and where I want to keep my job-search files. Handle the technical setup, help me customize how jobs are ranked, and give me LinkedIn search and email-alert instructions. Show me an example and where to review my leads. Ask before starting live searches, scheduling tasks or archiving email.

The **welcome wizard is a guided conversation**: you explain your needs, and the agent creates your private workspace and configuration. No manual configuration is needed beforehand. It will ask for any necessary file or service access.

If the agent cannot download the repository, use **Code → Download ZIP** on GitHub, extract it, and give the agent access to that folder to continue setup.

**The Indeed-connected scout (Bot4) is optional.** It uses Claude's Indeed search and full-job-detail connector. The ChatGPT Indeed app isn't supported by this workflow; bots1–3 can run in Codex or Cowork with the required tools.

## Run And Review

The wizard helps you choose a schedule, put the scouts in the right order and review a small trial before enabling recurring searches.

Your shortlist appears in `Leads/Yes` inside your chosen workspace. The agent shows you how to review matches, uncertainties and search coverage, and how to adjust your preferences as you learn what works. Your resume, preferences and results stay in that private workspace.

Details: [welcome wizard](docs/WELCOME.md) · [rubric](config/rubric.template.md) · [technical setup and workflow](docs/WORKFLOW.md) · [company sources](docs/COMPANIES_SCHEMA.md).
