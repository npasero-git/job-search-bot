import copy
import json
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
    return {"A": 47, "B": 24, "C": 18, "domain_adjustment": 0, "cap": None,
            "deductions": [{"points": 3, "clause": "Industrial protocol expertise",
                            "evidence": "Related instrumentation work; protocol depth partial."}]}


class SetupTests(unittest.TestCase):
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
            job = {"company":"Example", "title":"PM", "priority":"Apply"}
            with self.assertRaises(ValueError): io.write_lead(d, job, None)
            b = breakdown(); b.update(A=30, domain_adjustment=-15)
            b["deductions"] = [{"points":20, "clause":"Required domain", "evidence":"Absent"}]
            with self.assertRaises(ValueError): io.write_lead(d, job, b, threshold=50)

    def test_arithmetic_cap_and_duplicate_gap_mismatch(self):
        b = breakdown()
        self.assertEqual(io.validated_score(b), 89)
        b["cap"] = 70
        self.assertEqual(io.validated_score(b), 70)
        b["deductions"] *= 2
        with self.assertRaises(ValueError): io.validated_score(b)

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
                self.assertTrue(lead.name.startswith("89."))
                self.assertIn(source["content"], lead.read_text())
                self.assertNotIn("score_breakdown", lead.read_text())
                with self.assertRaises(FileExistsError): io.write_lead(p, job, breakdown())
                cid = "greenhouse:example-instruments:req-1"
                io.atomic_json(runtime/"role-ledger.json", {"version":1,"roles":[{"source_ids":[cid],"lead_file_path":str(lead)}]})
                io.atomic_json(runtime/"seen-jobs.json", {"seen_job_ids":[cid]})
                action["status"] = "consumed"
                io.atomic_json(runtime/"DISCOVERY-ACTIONS.json", {"version":1,"actions":[action]})
                io.atomic_json(runtime/"run-test-ats.json", {"status":"COMPLETE","score":89,"score_breakdown":breakdown()})
                self.assertIn(cid, json.loads((runtime/"seen-jobs.json").read_text())["seen_job_ids"])
                manual = io.write_lead(p, dict(job,title="Unresolved exact role"), None)
                self.assertTrue(manual.name.startswith("Manual Check"))
            self.assertFalse((runtime/".scout.lock").exists())


if __name__ == "__main__":
    unittest.main()
