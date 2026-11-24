# Workflow Contracts

## Installation And Task Setup

These are instructions for the setup agent; keep the user conversation in WELCOME concise. Do not recite this checklist during onboarding.

1. **Bootstrap from the whole package.** For a GitHub-link request, obtain the complete repository using the host's supported download or Git tools and permitted network access. Read AGENTS.md and this section before running setup, then guide the user through docs/WELCOME.md. A web-page excerpt is not a downloaded package. Verify scripts/config/skills/docs are present; extract a ZIP before using it. If downloading is unavailable, explain the specific limitation and ask the user to download/extract the repository and connect that folder. Do not bypass a network denial. Downloads may hold the source package, but is not the ongoing private workspace. Check for an available Python3.10+ interpreter; prefer a compatible existing or host-provided runtime. If unavailable, resolve the prerequisite with the user before installation. Keep version/command details out of onboarding unless they require user action.
2. **Establish one durable destination.** Offer a user-owned folder such as Documents/Employment/Job Scout and reuse the user's selection. Resolve the actual absolute path on the user's computer, not a cloud shell's home directory. Do not silently choose Downloads, an app's internal folder, a temporary directory, isolated worktree or session storage. An execution sandbox is fine if its file access demonstrably maps to the chosen durable folder. A familiar-looking pathname alone is not proof. Initialize only the scout subtree, not an unsolicited replica of someone's entire Employment structure; never overwrite an existing workspace.
3. **Verify access before installation.** Use the host's supported local-file/execution connection to create, read back and remove a uniquely named harmless probe in the selected parent/destination without modifying existing files. Explain and obtain the specific folder/tool approval if required. The setup script must execute against that verified host folder or verified durable mount; don't run it in a cloud shell and present that shell's output as a local installation. If access is denied/unavailable, stop dependent work and resume at the same path after resolution. No fallback workspace, copied runtime, broad permission disabling or destructive folder reconnection. The path validator prevents relative/checkout destinations; it cannot establish host-to-cloud storage mappings.
4. **Install and validate once.** Run init with the verified absolute destination, fill reviewed settings, validate, and read back the installed instructions/profile/state. All runtime paths and task prompts must point to that same workspace. Installed stage instructions/helpers run independently of the downloaded package; retain the package for maintenance or download it again later. Local setup and synthetic checks do not prove unattended access.
5. **Register tasks after the supervised trial and authorization.** Setup.py creates files, not chats, agents or schedules. Use the host's supported scheduling action, when available, for one task per enabled stage; inspect existing tasks before adding duplicates. Set every task's working folder to the private workspace and call its installed canonical stage file directly. Use local/project mode rather than separate Git worktrees when available. If the scheduler cannot be configured from chat, provide the exact prompts, folder, order and schedule for the user to enter. Do not claim tasks exist without readback. Do not launch all scouts simultaneously during installation.
6. **Check the scheduled execution context.** Test each configured stage's access to the same durable files/shared lock and required tools, sequentially, before relying on overnight operation. A grant in the setup chat does not establish permission in a new run. Verify least-privilege file/network/connector permissions, including separate email archiving consent, and report approvals that require user interaction. Inspect the first scheduled cycle for completed handoffs. If the current host cannot provide the shared filesystem/atomic locking contract, report that limitation rather than creating independent state or silently converting to a cloud architecture.

Host interfaces change. Use supported tools and current official guidance instead of fixed menu instructions or assumptions about permission inheritance. [ChatGPT/Codex scheduled-task guidance](https://learn.chatgpt.com/docs/automations?surface=app) distinguishes local project/worktree execution and unattended permissions. [Cowork scheduling](https://support.claude.com/en/articles/13854387-schedule-recurring-tasks-in-claude-cowork) and [local-file access](https://support.claude.com/en/articles/15520349-use-claude-cowork-on-web-desktop-and-mobile) distinguish cloud execution from access to connected computer folders. Cloud execution does not guarantee local access with the desktop app closed. Verify the user's actual plan/settings and access route; no universal promise of cloud-only or computer-off operation.

### Setup Commands And Review Handoff

From the complete package, use the verified interpreter and replace the example destination with the user's confirmed absolute path:

```sh
python3 scripts/setup.py init --workspace /absolute/private/job-scout
# Fill Instructions/settings.json in that workspace from the reviewed wizard answers.
python3 scripts/setup.py validate --workspace /absolute/private/job-scout
```

Do not run init over an existing workspace; follow Updating An Existing Workspace below. These commands are for the setup agent or an optional manual installation, not prerequisites the user must perform before the wizard.

During the guided trial, show the actual Leads/Yes path and walk through one lead's fit, gaps and unknowns. Explain where run reports show completed, partial, blocked or skipped coverage; a missing report is not zero results. Confirm the timezone, desired delivery time, enabled stages and each stage's actual schedule. Prefer finish-based sequencing if supported; otherwise stagger starts using observed durations plus a buffer. Gates do not queue skipped runs, and a due ATS sweep may proceed independently after upstream failure. Include any remaining user setup steps and how to request preference/rubric revisions. Review the first scheduled cycle before claiming dependable daily operation.

## Shared Behavior

Email writes signals, discovery verifies sources, ATS scores first-party jobs, and optional Indeed supplies fallback. All stages share one lock and durable paths. A blocked stage does not claim it ran; a due ATS sweep can work independently of a stalled signal stage. Catch-up runs should be sequential.

The public email stage has LinkedIn alerts and one general recent-job-alert search, with shared extraction rather than employer-specific configurations. Indeed is a Claude-only connector stage for this release, not a supported ChatGPT/Codex automation. If stages use different hosts, they must share the same durable workspace and lock; otherwise leave the optional stage disabled rather than maintaining divergent state.

The public prompts preserve first-party verification, source-bound evidence, bounded Workday variants, custom-source contracts, exact-ID deduplication, publication precedence, unknown-date manual checks, broad retrieval before location decisions, compact score calculations, existing caps, technical repair and partial coverage reporting.

Configuration replaces personal evidence, titles, geography, compensation, domain priorities, resume labels, company rankings, inbox queries and permissions. These differences are intentional. No retired dedicated pivot bot, personal application workflow, cloud transport or production schedules are installed.

## Created Workspace And Bot Outputs

Initialization creates this structure inside the selected private folder automatically:

```text
Job Scout/
  AGENTS.md
  Instructions/          Stage instructions, settings, profile and rubric
  Runtime/main/          Shared source configuration, queues and tracking
  Leads/
    Yes/                 Qualifying leads and promising unresolved manual checks
    No/                  Scored nonmatches or hard-skill failures
    WIP/                 Reserved for applications the user actually starts
    .archive/            Hidden historical, closed, stale and duplicate records
  .archive/run-receipts/  Hidden copies of superseded same-day run reports
  tools/                 Installed retrieval and persistence helpers
```

The folders exist before the first scout run. Setup seeds source configuration and empty processing/role-tracking state; it does not generate pretend leads. Signals, run reports, checkpoints and retrieved evidence are created as the corresponding work happens. All stages use this same workspace and shared lock.

| Stage | What it saves |
| --- | --- |
| 1. Email alerts | Signals, processed-message IDs and a run report in Runtime/main; no scored leads |
| 2. Web discovery | Verified source/job actions in the shared queue and a run report; promising unresolved exact roles may get a Manual Check file in Leads/Yes |
| 3. ATS | Full-JD lead files in Yes/No, source evidence, role/duplicate tracking, coverage and run reports |
| 4. Indeed, if enabled | The same lead/tracking structure as ATS, plus its fallback coverage report and discovery actions |

Yes uses the user's configured review threshold, subject to eligibility and evidence checks. Unscored manual checks are labeled explicitly. There is no Maybe queue. Scouts do not move a lead to WIP merely because it looks attractive, or infer that an application was submitted. Human-facing leads contain the full JD and a concise fit assessment; detailed calculations and diagnostics stay in run records. Startup does not create resumes, applications or unrelated employment records.

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

Developer checks: run `python3 -m unittest discover -s tests -v` from the repository. Tests are offline development checks, not steps for scheduled scouts.

Offline tests cover setup, lock ownership, arithmetic, source identity, bounded pagination, publication handling and synthetic persistence. They do not test live email mutation, every current career endpoint, unattended scheduling or model interpretation accuracy. Source notes are contracts to verify, not guarantees of current availability.

## Updating An Existing Workspace

Do not rerun init over existing files. Review the current rubric and weights through the wizard, replace the retired absent_preferred_score setting with the chosen weights, and update scoring instructions and the arithmetic helper together. Preserve leads, receipts, ledgers and source configuration. Historical A/B/C scores are not fit-v2 scores; do not mechanically regrade them. Validation rejects the retired setting rather than silently changing its meaning.

Setup copies skills and the rubric to Instructions, public source examples to Runtime/main, and retrieval/arithmetic helpers to tools. Settings remain authoritative for user choices; validation derives candidate-profile.md from their profile fields. Keep that workspace outside the checkout. Initialization installs no connectors, cloud services or schedules. Authorize service connections separately and verify a supervised run before recurring work.
