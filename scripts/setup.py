"""Initialize/validate a private workspace. Never calls a connector or schedules work."""
import argparse
import json
import re
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo
from scout_io import RunLock, atomic_text, validate_weights

REPO = Path(__file__).resolve().parents[1]


def unresolved(value):
    return bool(re.search(r"\{\{[^}]+\}\}|\bTODO\b", json.dumps(value)))


def validate_settings(s):
    if s.get("setup_reviewed") is not True or unresolved(s):
        raise ValueError("Complete required answers and explicitly confirm setup_reviewed")
    ZoneInfo(s["timezone"])
    p = s["profile"]
    if not isinstance(p["summary"], str) or not p["summary"].strip():
        raise ValueError("A factual profile summary is required")
    for key in ("evidence", "resume_variants"):
        if not isinstance(p[key], list) or not p[key] or any(not isinstance(x, str) or not x.strip() for x in p[key]):
            raise ValueError("Profile " + key + " must contain meaningful strings")
    if not isinstance(p["gaps"], list) or any(not isinstance(x, str) for x in p["gaps"]):
        raise ValueError("Invalid profile gaps")
    for key in ("include", "exclude"):
        if not isinstance(s["titles"][key], list) or any(not isinstance(x, str) or not x.strip() for x in s["titles"][key]):
            raise ValueError("Invalid title list")
    if not s["titles"]["include"]:
        raise ValueError("At least one target title is required")
    for key in ("email_enabled", "archive_email", "indeed_enabled"):
        if type(s["tools"][key]) is not bool:
            raise ValueError("Tool permissions must be boolean")
    if s["tools"]["archive_email"] and not s["tools"]["email_enabled"]:
        raise ValueError("Archiving requires email to be enabled")
    if "absent_preferred_score" in s:
        raise ValueError("Retired absent_preferred_score: review the welcome wizard and configure weights")
    validate_weights(s["weights"])
    for key, high in (("freshness_days", 365), ("review_threshold", 100)):
        if type(s[key]) is not int or not 0 <= s[key] <= high:
            raise ValueError("Invalid " + key)
    for key in ("web_search_calls", "web_fetch_calls", "new_actions", "company_recovery", "optional_queries", "indeed_calls"):
        if type(s["budgets"][key]) is not int or s["budgets"][key] < 0:
            raise ValueError("Invalid budget " + key)
    floor = s["compensation"]["base_floor"]
    if floor is not None and (type(floor) not in (int, float) or not 0 <= floor < 1000000000):
        raise ValueError("Invalid base floor; null means unknown")
    if not isinstance(s["compensation"]["currency"], str) or not s["compensation"]["currency"].strip():
        raise ValueError("Currency is required")
    for group, keys in (("geography", ("countries", "metros")),
                        ("domains", ("prioritize", "adjacent", "exclude")),
                        ("compensation", ("employment_types",))):
        for key in keys:
            if not isinstance(s[group][key], list) or any(not isinstance(x, str) or not x.strip() for x in s[group][key]):
                raise ValueError("Invalid " + group + "." + key)
    for key in ("soft_preferences", "discovery_queries"):
        if not isinstance(s[key], list) or any(not isinstance(x, str) or not x.strip() for x in s[key]):
            raise ValueError("Invalid " + key)
    for key in ("remote", "relocation"):
        if s["geography"][key] not in ("yes", "no", "unknown", "conditional"):
            raise ValueError("Use yes/no/unknown/conditional for " + key)
    return s


def private_path(path):
    path = Path(path).expanduser().resolve()
    if path == REPO or REPO in path.parents:
        raise ValueError("Private workspace must be outside the public checkout")
    return path


def initialize(path):
    path = private_path(path)
    path.mkdir(parents=True, exist_ok=False)
    for folder in ("Instructions", "Runtime/main", "Leads/Yes", "Leads/No", "Leads/WIP", "Leads/.archive", ".archive/run-receipts", "tools"):
        (path / folder).mkdir(parents=True, exist_ok=True)
    for src in [REPO / "AGENTS.md", *sorted((REPO / "skills").glob("*.md"))]:
        dest = path / ("AGENTS.md" if src.name == "AGENTS.md" else "Instructions/" + src.name)
        dest.write_text(src.read_text().replace("{{WORKSPACE}}", str(path)))
    for src, dst in {
        "settings.example.json": "Instructions/settings.json",
        "candidate-profile.example.md": "Instructions/candidate-profile.md",
        "rubric.template.md": "Instructions/rubric.md",
        "companies.example.json": "Runtime/main/companies.json",
        "email-alert-sources.example.json": "Runtime/main/email-alert-sources.json",
        "discovery-actions.example.json": "Runtime/main/DISCOVERY-ACTIONS.json",
        "role-ledger.example.json": "Runtime/main/role-ledger.json",
    }.items():
        shutil.copy2(REPO / "config" / src, path / dst)
    for name, data in (("seen-jobs.json", {"seen_job_ids": []}),
                       ("linkedin-processed.json", {"processed_message_ids": [], "last_run": None})):
        (path / "Runtime/main" / name).write_text(json.dumps(data) + "\n")
    for name in ("ats_fetch.py", "scout_io.py"):
        shutil.copy2(REPO / "scripts" / name, path / "tools" / name)
    return path


def _validate_workspace(path):
    path = private_path(path)
    s = validate_settings(json.loads((path / "Instructions/settings.json").read_text()))
    for name, list_key in (("companies.json", None), ("DISCOVERY-ACTIONS.json", "actions"),
                           ("role-ledger.json", "roles"), ("seen-jobs.json", "seen_job_ids"),
                           ("linkedin-processed.json", "processed_message_ids")):
        value = json.loads((path / "Runtime/main" / name).read_text())
        if unresolved(value):
            raise ValueError("Unfilled runtime placeholder: " + name)
        rows = value if list_key is None else value.get(list_key) if isinstance(value, dict) else None
        if not isinstance(rows, list):
            raise ValueError("Expected list in " + name)
        if list_key in (None, "actions", "roles") and any(not isinstance(row, dict) for row in rows):
            raise ValueError("Expected records in " + name)
    sources = json.loads((path / "Runtime/main/email-alert-sources.json").read_text())
    if not isinstance(sources.get("sources"), list) or type(sources.get("max_total_threads_per_run")) is not int or sources["max_total_threads_per_run"] <= 0:
        raise ValueError("Invalid email source list or total limit")
    if s["tools"]["email_enabled"] and not sources["sources"]:
        raise ValueError("Email enabled without approved sources")
    for source in sources["sources"]:
        query = source["gmail_query"]
        scoped = (re.search(r"(?:^|[\s{])from:\S", query)
                  or "label:job-scout-alert" in query
                  or re.search(r'subject:"(?:job alerts?|new jobs|new roles|new openings|job opportunities)"', query))
        if unresolved(source) or not scoped or not ("newer_than:" in query or "after:" in query):
            raise ValueError("Email query needs a sender/alert label/job-alert subject and time bound")
        if type(source["max_threads"]) is not int or source["max_threads"] <= 0:
            raise ValueError("Invalid email source limit")
        if type(source.get("archive_after_processing")) is not bool:
            raise ValueError("Email archive permission must be explicit")
    text = (REPO / "config/candidate-profile.example.md").read_text()
    for key, value in {
        "PROFILE_SUMMARY": s["profile"]["summary"],
        "PROFILE_EVIDENCE": "\n".join("- " + x for x in s["profile"]["evidence"]),
        "PROFILE_GAPS": "\n".join("- " + x for x in s["profile"]["gaps"]) or "Not yet assessed; do not infer absence or expertise.",
    }.items():
        text = text.replace("{{" + key + "}}", value)
    for file in (path / "Instructions").glob("*.md"):
        if unresolved(text if file.name == "candidate-profile.md" else file.read_text()):
            raise ValueError("Unfilled instruction placeholder: " + file.name)
    atomic_text(path / "Instructions/candidate-profile.md", text)
    return s


def validate_workspace(path):
    path = private_path(path)
    with RunLock(path / "Runtime/main", "setup-validation"):
        return _validate_workspace(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init", "validate"])
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            print(initialize(args.workspace))
            print("Created private workspace. Complete settings, then validate; no live work performed.")
        else:
            validate_workspace(args.workspace)
            print("Configuration valid. Unknown choices remain review questions; tool access is not yet proven.")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")
