# Welcome To Job Scout

Start with the work you want and the experience you bring. Short answers are enough; “unknown” is fine. Your answers stay in a private workspace outside this repository.

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

**Indeed is optional and Claude-only for this release.** Bot4 needs Claude's Indeed search and full-job-detail connector. The ChatGPT Indeed app isn't a supported replacement; use bots1–3 in ChatGPT/Codex.

## 6. Review And Start Small

Choose a permanent folder on your computer, such as Documents/Employment/Job Scout, and a timezone. The agent checks access there before installing or scheduling anything. If access fails, resolve it in the app; setup must not silently switch folders. Confirm your profile, constraints and rubric, and choose email/archive permissions; archiving starts off.

Your final setup summary should contain:

- Your target work, constraints and unresolved choices.
- The saved private workspace and your chosen rubric.
- Your LinkedIn search/alert instructions and any pending delivery check.
- Email permissions and either “Indeed disabled” or “Claude Indeed connector verified.”

Follow the [setup and validation commands](../README.md#start-here), inspect a synthetic example, then approve a small supervised run. Review a real lead before scheduling recurring work. The scouts never apply or contact employers for you.

**Scheduling:** the normal order is **1. Email alerts → 2. Web discovery → 3. Company job boards → 4. Indeed, if enabled.** Start each after the previous stage finishes where your scheduler supports it; otherwise space start times using observed run durations and allow a buffer. Choose your timezone and preferred morning delivery time during setup.

The gates prevent premature or duplicate work; they don't queue a blocked run for later. Check skipped/failed stages after the first scheduled cycle. A due daily company-board sweep can still run if upstream work fails, so one failure needn't stop all coverage. See [run-order details](../README.md#run-and-review).
