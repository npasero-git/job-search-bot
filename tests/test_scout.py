import copy
import json
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ats_fetch as ats
import scout_io as io
import setup

CONFIG = {"provider": "workday", "host": "example.myworkdayjobs.com",
          "tenant": "example", "site": "External", "pagination_max_pages": 3}


def page(start, total=55, count=None):
    count = min(20, total-start) if count is None else count
    return {"ok": True, "data": {"total": total if start == 0 else 0,
            "jobPostings": [{"title": "Product Manager", "externalPath": "/job/PM_JR"+str(i)}
                            for i in range(start, start+count)]}}


def settings():
    s = json.loads((setup.REPO / "config/settings.example.json").read_text())
    s["setup_reviewed"] = True
    s["profile"].update(summary="Product manager for industrial measurement systems.",
        evidence=["Owned sensor-product requirements and customer launches.", "Completed an MBA."],
        gaps=["No production model-serving ownership."])
    return s


def breakdown():
    return {"rubric_version": "fit-v2", "A": 47, "B": 24, "D": 12, "T": 8, "S": 9, "K": 3,
            "preferred_status": "present", "full_jd": True, "cap": None,
            "deductions": [{"points": 3, "clause": "Industrial protocol expertise",
                            "evidence": "Related instrumentation work; protocol depth partial."}]}


class SetupTests(unittest.TestCase):
    def test_relative_destination_cannot_follow_agent_working_directory(self):
        for path in ("workspace", ".", "../Employment/Job Scout"):
            with self.assertRaises(ValueError): setup.private_path(path)

    def test_downloaded_package_installs_independent_durable_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            package = root / "Downloads/job-search-bot"
            shutil.copytree(setup.REPO, package, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            workspace = root / "Documents/Employment/Job Scout"
            command = [sys.executable, str(package / "scripts/setup.py")]
            subprocess.run(command + ["init", "--workspace", str(workspace)],
                           cwd=package.parent, check=True, capture_output=True, text=True)
            io.atomic_json(workspace / "Instructions/settings.json", settings())
            subprocess.run(command + ["validate", "--workspace", str(workspace)],
                           cwd=package.parent, check=True, capture_output=True, text=True)
            self.assertFalse((package / "Runtime").exists())
            for stage in (workspace / "Instructions").glob("SKILL-*.md"):
                self.assertIn(str(workspace), stage.read_text())
                self.assertNotIn("{{WORKSPACE}}", stage.read_text())
            shutil.rmtree(package)  # Only the disposable test copy in Downloads.
            subprocess.run([sys.executable, "-c", "import ats_fetch, scout_io"],
                           cwd=workspace / "tools", check=True, capture_output=True, text=True)
            self.assertTrue((workspace / "Runtime/main/role-ledger.json").exists())

    def test_missing_placeholders_fail(self):
        raw = json.loads((setup.REPO / "config/settings.example.json").read_text())
        with self.assertRaises(ValueError): setup.validate_settings(raw)
        raw["setup_reviewed"] = True
        with self.assertRaises(ValueError): setup.validate_settings(raw)

    def test_missing_profile_and_invalid_budget_fail(self):
        for key, value in (("profile", {}), ("budgets", {"web_search_calls": -1})):
            s = settings(); s[key] = value
            with self.assertRaises((ValueError, KeyError)): setup.validate_settings(s)

    def test_unknowns_not_invented(self):
        s = setup.validate_settings(settings())
        self.assertIsNone(s["compensation"]["base_floor"])
        self.assertEqual(s["geography"]["remote"], "unknown")
        self.assertFalse(s["tools"]["archive_email"])

    def test_no_private_runtime_inside_repo(self):
        with self.assertRaises(ValueError): setup.private_path(setup.REPO / "private")

    def test_init_refuses_overwrite_and_email_requires_allowlist(self):
        with tempfile.TemporaryDirectory() as d:
            p = setup.initialize(Path(d) / "workspace")
            with self.assertRaises(FileExistsError): setup.initialize(p)
            s = settings(); s["tools"]["email_enabled"] = True
            io.atomic_json(p / "Instructions/settings.json", s)
            io.atomic_json(p / "Runtime/main/email-alert-sources.json",
                           {"sources":[], "max_total_threads_per_run":20})
            with self.assertRaises(ValueError): setup.validate_workspace(p)
            self.assertFalse((p / "Runtime/main/.scout.lock").exists())

    def test_validation_respects_existing_writer(self):
        with tempfile.TemporaryDirectory() as d:
            p = setup.initialize(Path(d) / "workspace")
            with io.RunLock(p / "Runtime/main", "existing") as lock:
                before = (lock.path / "owner.json").read_bytes()
                with self.assertRaises(FileExistsError): setup.validate_workspace(p)
                self.assertEqual(before, (lock.path / "owner.json").read_bytes())

    def test_malformed_state_does_not_replace_profile(self):
        with tempfile.TemporaryDirectory() as d:
            p = setup.initialize(Path(d) / "workspace")
            io.atomic_json(p / "Instructions/settings.json", settings())
            before = (p / "Instructions/candidate-profile.md").read_bytes()
            io.atomic_json(p / "Runtime/main/role-ledger.json", {"roles": {}})
            with self.assertRaises(ValueError): setup.validate_workspace(p)
            self.assertEqual(before, (p / "Instructions/candidate-profile.md").read_bytes())
            self.assertFalse((p / "Runtime/main/.scout.lock").exists())

    def test_email_permission_is_explicit_and_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            p = setup.initialize(Path(d) / "workspace")
            s = settings(); s["tools"]["email_enabled"] = True
            io.atomic_json(p / "Instructions/settings.json", s)
            source = {"id":"example", "gmail_query":"from:jobs@example.test newer_than:2d",
                      "archive_after_processing":False, "max_threads":5}
            for query, archive in (("in:inbox", False), (source["gmail_query"], "false")):
                bad = dict(source, gmail_query=query, archive_after_processing=archive)
                io.atomic_json(p / "Runtime/main/email-alert-sources.json",
                               {"sources":[bad], "max_total_threads_per_run":20})
                with self.assertRaises(ValueError): setup.validate_workspace(p)
            io.atomic_json(p / "Runtime/main/email-alert-sources.json",
                           {"sources":[source], "max_total_threads_per_run":20})
            setup.validate_workspace(p)

    def test_generic_job_alert_search_and_negative_sender(self):
        with tempfile.TemporaryDirectory() as d:
            p = setup.initialize(Path(d) / "workspace")
            s = settings(); s["tools"]["email_enabled"] = True
            io.atomic_json(p / "Instructions/settings.json", s)
            setup.validate_workspace(p)
            source_file = p / "Runtime/main/email-alert-sources.json"
            config = json.loads(source_file.read_text())
            self.assertEqual(len(config["sources"]), 2)
            self.assertTrue(all(not x["archive_after_processing"] for x in config["sources"]))
            config["sources"][1]["gmail_query"] = 'newer_than:2d in:inbox -from:linkedin.com'
            io.atomic_json(source_file, config)
            with self.assertRaises(ValueError): setup.validate_workspace(p)
            config["sources"][1]["gmail_query"] = 'in:inbox subject:"new jobs"'
            io.atomic_json(source_file, config)
            with self.assertRaises(ValueError): setup.validate_workspace(p)


class RetrievalTests(unittest.TestCase):
    def test_three_pages_later_zero_and_cap(self):
        calls = []
        def fetch(url, body):
            calls.append(body)
            return page(body["offset"])
        result = ats.workday_company({"category":"Semiconductor"}, CONFIG, fetcher=fetch)
        self.assertTrue(result["complete"])
        self.assertEqual(len(calls), 24)
        self.assertEqual(len(result["jobs"]), 55)
        capped = ats.workday_company({}, CONFIG, fetcher=lambda u,b: page(b["offset"], 100))
        self.assertFalse(capped["complete"])
        self.assertTrue(all(v["pages"] == 3 for v in capped["variants"].values()))

    def test_first_page_only_default(self):
        config = dict(CONFIG); config.pop("pagination_max_pages")
        result = ats.workday_company({}, config, fetcher=lambda u,b: page(b["offset"]))
        self.assertFalse(result["complete"])
        self.assertTrue(all(v["pages"] == 1 for v in result["variants"].values()))

    def test_inactive_never_fetched(self):
        for company, config in (({"active":False}, CONFIG), ({}, dict(CONFIG, active=False))):
            result = ats.workday_company(company, config,
                       fetcher=lambda u,b: self.fail("Inactive source fetched"))
            self.assertEqual(result["skipped"], "inactive")
            self.assertFalse(result["complete"])

    def test_malformed_duplicate_count_and_empty(self):
        for data in ({"total":1,"jobPostings":[{}]},
                     {"total":2,"jobPostings":[{"title":"PM","externalPath":"/1"}]*2},
                     {"total":True,"jobPostings":[]}):
            with self.assertRaises(ValueError): ats.workday_page(data, [])
        with self.assertRaises(ValueError): ats.workday_page(dict(page(20, 30)["data"], total=30), [], 55)
        self.assertFalse(ats.workday_page({"total":0,"jobPostings":[]}, [])["complete"])

    def test_publication_beats_update_and_null(self):
        self.assertEqual(ats.greenhouse_date({"first_published_at":"2001-01-01", "updated_at":"2026-11-24"}),
                         ("2001-01-01", "first_published_at"))
        self.assertEqual(ats.greenhouse_date({"first_published_at":None, "updated_at":"2026-11-24"}),
                         ("2026-11-24", "updated_at"))
        self.assertEqual(ats.greenhouse_date({}), (None, "unknown"))

    def test_cache_is_source_bound_and_resume_skips_finished(self):
        with tempfile.TemporaryDirectory() as d:
            one = {"provider":"greenhouse","slug":"example-one"}
            two = {"provider":"greenhouse","slug":"example-two"}
            p = ats.save_response(d, "run", one, {}, {"jobs":[1]})
            with self.assertRaises(ValueError): ats.read_response(p, two)
            self.assertEqual(ats.read_response(p, one), {"jobs":[1]})
        result = ats.workday_company({}, CONFIG, fetcher=lambda u,b: page(0, 1))
        self.assertEqual(ats.workday_company({},CONFIG,prior=result,
                         fetcher=lambda u,b:self.fail("Repeated work")), result)


class PersistenceTests(unittest.TestCase):
    def test_unscored_or_hard_floor_cannot_be_apply(self):
        with tempfile.TemporaryDirectory() as d:
            p = setup.initialize(Path(d) / "workspace")
            s = settings(); s["review_threshold"] = 10
            io.atomic_json(p / "Instructions/settings.json", s)
            job = {"company":"Example", "title":"PM", "priority":"Apply"}
            with self.assertRaises(ValueError): io.write_lead(p, job, None)
            b = breakdown(); b.update(A=10)
            b["deductions"] = [{"points":20, "clause":"Required capability " + str(i), "evidence":"Absent"} for i in range(2)]
            with self.assertRaises(ValueError): io.write_lead(p, job, b)

    def test_arithmetic_cap_and_duplicate_gap_mismatch(self):
        b = breakdown()
        self.assertEqual(io.validated_score(b, settings()["weights"]), 88.8)
        b["cap"] = 70
        self.assertEqual(io.validated_score(b, settings()["weights"]), 70)
        b["deductions"] *= 2
        with self.assertRaises(ValueError): io.validated_score(b, settings()["weights"])

    def test_exact_absence_proration_and_custom_weights(self):
        b = breakdown(); b.update(B=None, preferred_status="absent")
        self.assertAlmostEqual(io.validated_score(b, settings()["weights"]), 964/11)
        w = dict(required=30, preferred=30, domain=20, trajectory=10, scope=5, company=5)
        self.assertAlmostEqual(io.validated_score(b, w), 86.22)
        # Increasing scope by one raw point still adds exactly its unchanged weight fraction.
        b["S"] = 10
        self.assertAlmostEqual(io.validated_score(b, w), 86.72)

    def test_absent_unknown_unmet_are_distinct_and_caps_are_last(self):
        b = breakdown(); b.update(B=None, preferred_status="absent", cap=70)
        self.assertEqual(io.validated_score(b, settings()["weights"]), 70)
        b.update(full_jd=False)
        with self.assertRaises(ValueError): io.validated_score(b, settings()["weights"])
        b.update(preferred_status="unknown", cap=None)
        self.assertEqual(io.validated_score(b, settings()["weights"]), 60)
        b.update(preferred_status="present", B=0, full_jd=True)
        self.assertEqual(io.validated_score(b, settings()["weights"]), 69.6)

    def test_invalid_weights_and_legacy_receipts_rejected(self):
        for field, value in (("required", -1), ("preferred", True), ("scope", float("nan")), ("domain", float("inf"))):
            s = settings(); s["weights"][field] = value
            with self.assertRaises(ValueError): setup.validate_settings(s)
        for w in (dict(required=0, preferred=75, domain=0, trajectory=10, scope=10, company=5),
                  dict(required=40, preferred=20, domain=15, trajectory=10, scope=10, company=0)):
            with self.assertRaises(ValueError): io.validate_weights(w)
        s = settings(); s["absent_preferred_score"] = 15
        with self.assertRaises(ValueError): setup.validate_settings(s)
        for change in ({"C":18}, {"domain_adjustment":-15}, {"rubric_version":"old"}):
            b = dict(breakdown(), **change)
            with self.assertRaises(ValueError): io.validated_score(b, settings()["weights"])
        b = breakdown(); b["weights"] = dict(settings()["weights"], required=45)
        with self.assertRaises(ValueError): io.validated_score(b, settings()["weights"])

    def test_zero_preferred_and_fractional_custom_weights(self):
        w = dict(required=42.5, preferred=0, domain=27.5, trajectory=10, scope=15, company=5)
        present = io.validated_score(breakdown(), w)
        b = breakdown(); b.update(B=None, preferred_status="absent")
        self.assertEqual(io.validated_score(b, w), present)
        b.update(A=50, D=15, T=10, S=10, K=5, deductions=[])
        self.assertEqual(io.validated_score(b, w), 100)

    def test_writer_uses_custom_settings_and_unrounded_threshold(self):
        with tempfile.TemporaryDirectory() as d:
            p = setup.initialize(Path(d) / "private")
            s = settings(); s["weights"].update(required=30, preferred=30, domain=20, trajectory=10, scope=5, company=5)
            io.atomic_json(p / "Instructions/settings.json", s)
            setup.validate_workspace(p)
            b = breakdown(); b.update(B=None, preferred_status="absent")
            job = dict(company="Example", title="PM", listing_url="https://example.test/1", summary="Synthetic", priority="Review")
            path = io.write_lead(p, job, b)
            self.assertTrue(path.name.startswith("86.22."))
            self.assertEqual(json.loads((p / "Instructions/settings.json").read_text())["weights"], s["weights"])
            io.atomic_json(p / "Instructions/settings.json", settings())
            b = breakdown(); b.update(B=0, D=12.399)
            path = io.write_lead(p, dict(job, title="Boundary PM"), b)
            self.assertEqual(path.parent.name, "No")
            self.assertTrue(path.name.startswith("69.99."))

    def test_wrong_lock_owner_not_released(self):
        with tempfile.TemporaryDirectory() as d:
            lock = io.RunLock(d, "one"); lock.__enter__()
            io.atomic_json(lock.path/"owner.json", {"stage":"other"})
            with self.assertRaises(RuntimeError): lock.__exit__()
            self.assertTrue(lock.path.exists())

    def test_synthetic_new_user_signal_to_lead(self):
        with tempfile.TemporaryDirectory() as d:
            p = setup.initialize(Path(d) / "private")
            io.atomic_json(p / "Instructions/settings.json", settings())
            setup.validate_workspace(p)
            self.assertFalse(setup.unresolved((p / "Instructions/candidate-profile.md").read_text()))
            runtime = p / "Runtime/main"
            with io.RunLock(runtime, "synthetic-integration"):
                # Mock adapter outputs: no email/API calls or claimed model evaluation.
                signal = {"company":"Example Instruments", "title":"Product Manager",
                          "source_url":"https://example.test/jobs/req-1", "source_id":"alert:1"}
                io.atomic_json(runtime / "run-test-linkedin.json", {"status":"COMPLETE","signals":[signal]})
                action = dict(signal, id="exact-1", action="verify_exact_job", status="verified", target_skill="ats")
                io.atomic_json(runtime / "DISCOVERY-ACTIONS.json", {"version":1,"actions":[action]})
                config = {"provider":"greenhouse","slug":"example-instruments"}
                source = {"id":"req-1", "title":signal["title"], "content":"Own industrial sensor roadmaps. MBA preferred."}
                evidence = ats.save_response(runtime / "evidence", "test", config, {}, source)
                self.assertEqual(ats.read_response(evidence, config), source)
                job = dict(signal, listing_url=signal["source_url"], summary="Supported sensor product ownership.",
                           description=source["content"], gaps="Protocol depth partial; work location unresolved.",
                           priority="Review")
                lead = io.write_lead(p, job, breakdown())
                self.assertTrue(lead.name.startswith("88.8."))
                self.assertIn(source["content"], lead.read_text())
                self.assertNotIn("score_breakdown", lead.read_text())
                with self.assertRaises(FileExistsError): io.write_lead(p, job, breakdown())
                cid = "greenhouse:example-instruments:req-1"
                io.atomic_json(runtime/"role-ledger.json", {"version":1,"roles":[{"source_ids":[cid],"lead_file_path":str(lead)}]})
                io.atomic_json(runtime/"seen-jobs.json", {"seen_job_ids":[cid]})
                action["status"] = "consumed"
                io.atomic_json(runtime/"DISCOVERY-ACTIONS.json", {"version":1,"actions":[action]})
                io.atomic_json(runtime/"run-test-ats.json", {"status":"COMPLETE","score":88.8,"score_breakdown":breakdown(),"weights":settings()["weights"]})
                self.assertIn(cid, json.loads((runtime/"seen-jobs.json").read_text())["seen_job_ids"])
                manual = io.write_lead(p, dict(job,title="Unresolved exact role"), None)
                self.assertTrue(manual.name.startswith("Manual Check"))
            self.assertFalse((runtime/".scout.lock").exists())


if __name__ == "__main__":
    unittest.main()
