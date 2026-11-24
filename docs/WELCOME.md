# Welcome To Job Scout

Your agent guides you through these questions and handles the technical setup. Start with the work you want and the experience you bring. Short answers are enough; “unknown” is fine. Your answers stay in a private workspace outside this repository.

## 1. Your Next Role

What work would you like to own? Which roles or industries interest you? Individual-contributor work, people management, or either? Distinguish firm exclusions from preferences.

## 2. Your Experience

Share a resume or a few examples of products, decisions and outcomes you owned. What adjacent work could you credibly move into? Distinguish advising, learning and prototyping from shipped work. Keep resumes and confidential documents private.

## 3. Practical Constraints

Where can you work, and where would you consider living? What are your work-authorization, onsite/remote, employment-type and minimum-base-pay requirements? Leave undecided choices open.

## 4. What Makes A Good Match?

Which matters most: matching your experience, moving into a new field, owning broader decisions, or joining particular kinds of companies? Let those needs shape the rubric.

Start here, then customize:

| Component | Starting weight |
| --- | ---: |
| Required qualifications |40|
| Preferred qualifications |20|
| Domain fit |15|
| Career direction and interest |10|
| Actual role scope |10|
| Company preference |5|

You don't need to pick numbers yourself. Explain what matters more or less and review the proposed balance. Pay stays a practical constraint; titles and company fame don't establish fit. When a posting lists no preferred qualifications, their weight shifts proportionally to qualifications and domain; other priorities stay unchanged.

Review a strong match versus an attractive stretch role, then agree on your rubric and shortlist selectivity. Optional [calculation details](../config/rubric.template.md) are separate.

## 5. Where Leads Come From

Choose useful companies from the starter list. Bots1–3 read job-alert emails, discover listings and check company job boards. Email coverage is LinkedIn plus a general recent-job-alert search; no employer-by-employer setup is needed.

**Your setup includes copy-ready LinkedIn Jobs searches**, locations and useful filters: a broad role search plus a few complementary domain searches.

**Put these searches into LinkedIn Jobs and turn on daily email alerts so Bot1 has emails to read.** Review the results first; see [LinkedIn's alert settings](https://www.linkedin.com/help/linkedin/answer/a1420165). Check that the bot finds the first delivered alert.

**The Indeed-connected scout (Bot4) is optional and Claude-only for this release.** It needs Claude's Indeed search and full-job-detail connector. The ChatGPT Indeed app isn't a supported replacement; use bots1–3 in Codex or Cowork with the required tools.

## 6. Review And Start Small

Where would you like to keep your job-search files? For example, Documents/Employment/Job Scout. What timezone and morning delivery time would you prefer? Your agent confirms the folder and checks access before setting it up. Confirm your profile, constraints and rubric, and choose email/archive permissions; archiving starts off.

Your final setup summary should contain:

- Your target work, constraints and unresolved choices.
- The saved private workspace and your chosen rubric.
- Your LinkedIn search/alert instructions and any pending delivery check.
- Email permissions and either “Indeed disabled” or “Claude Indeed connector verified.”
- The proposed run order and schedule, whether tasks are enabled, and any remaining setup steps.
- Where to review leads and search coverage, and how to change your preferences.

Your agent completes and checks the setup, then shows you a synthetic example. Approve a small supervised search and review a real lead before scheduling recurring work. The scouts never apply or contact employers for you.

**Scheduling:** the normal order is **1. Email alerts → 2. Web discovery → 3. Company job boards → 4. Indeed-connected scout, if enabled.** Your agent arranges that order using the scheduler's available controls and the time each stage needs. It reports anything you must finish in the app.

**Reviewing results:** open `Leads/Yes` in your chosen folder. Your agent walks through the fit assessment, important gaps and any missing information, then shows which sources ran or were blocked. After the first scheduled cycle, check for skipped or failed stages before relying on daily coverage. Tell the agent when matches are off-target so you can review changes to your preferences or rubric together.
