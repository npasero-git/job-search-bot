"""Small local persistence and arithmetic helpers; no search or model judgment."""
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path


def atomic_text(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix="." + path.name)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        if path.read_text() != raw:
            raise ValueError("File readback mismatch")
    finally:
        Path(name).unlink(missing_ok=True)


def atomic_json(path, data):
    atomic_text(path, json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


class RunLock:
    def __init__(self, runtime, stage):
        self.path = Path(runtime) / ".scout.lock"
        self.owner = {"stage": stage, "run_id": uuid.uuid4().hex,
                      "started_at": datetime.now(timezone.utc).isoformat()}

    def __enter__(self):
        self.path.mkdir()  # Failed acquisition must not write another owner's metadata.
        try:
            atomic_json(self.path / "owner.json", self.owner)
        except BaseException:
            (self.path / "owner.json").unlink(missing_ok=True)
            self.path.rmdir()
            raise
        return self

    def __exit__(self, *args):
        path = self.path / "owner.json"
        if json.loads(path.read_text()) != self.owner:
            raise RuntimeError("Lock ownership changed; refusing release")
        path.unlink()
        self.path.rmdir()


def validated_score(breakdown):
    for name, upper in (("A", 50), ("B", 25), ("C", 25)):
        value = breakdown[name]
        if type(value) is not int or not 0 <= value <= upper:
            raise ValueError("Invalid " + name)
    deductions = breakdown["deductions"]
    if not isinstance(deductions, list):
        raise ValueError("Deductions must be a list")
    for item in deductions:
        if item.get("points") not in (3, 20) or not item.get("clause") or not item.get("evidence"):
            raise ValueError("Unsupported deduction or missing evidence")
    if breakdown["A"] != max(0, 50 - sum(x["points"] for x in deductions)):
        raise ValueError("Required-score arithmetic mismatch")
    adjustment = breakdown.get("domain_adjustment", 0)
    if type(adjustment) is not int or adjustment not in (0, -15):
        raise ValueError("Invalid domain adjustment")
    cap = breakdown.get("cap")
    if cap is not None and (type(cap) is not int or not 0 <= cap <= 100):
        raise ValueError("Invalid cap")
    total = max(0, breakdown["A"] + adjustment) + breakdown["B"] + breakdown["C"]
    return min(total, cap) if cap is not None else total


def write_lead(workspace, job, breakdown, threshold=70):
    """Caller holds the lock and verifies gates/dedup; receipts retain the calculation."""
    score = validated_score(breakdown) if breakdown is not None else None
    folder = "Yes" if score is None or score >= threshold else "No"
    if breakdown is not None and max(0, breakdown["A"] + breakdown.get("domain_adjustment", 0)) <= 15:
        folder = "No"
    if job.get("priority") == "Apply" and (score is None or folder != "Yes"):
        raise ValueError("Ineligible Apply disposition")
    label = re.sub(r'[^\w .()-]', "_", job["company"] + " - " + job["title"]).strip(". ")[:160]
    if not label:
        raise ValueError("Missing role label")
    filename = (str(score) + ". " if score is not None else "Manual Check - ") + label + ".md"
    path = Path(workspace) / "Leads" / folder / filename
    content = (f'# {job["title"]} @ {job["company"]}\n\n'
               f'**Score:** {score if score is not None else "Unscored"}\n'
               f'**Priority:** {job.get("priority", "Review")}\n'
               f'**Listing:** {job["listing_url"]}\n'
               f'**Location:** {job.get("location", "Unknown")}\n'
               f'**Posted:** {job.get("posted", "Unknown")}\n'
               f'**Compensation:** {job.get("compensation", "Unverified")}\n'
               f'**Resume:** {job.get("resume", "Primary")}\n\n'
               f'## Fit\n{job["summary"]}\n\n'
               f'## Gaps And Questions\n{job.get("gaps", "None established")}\n\n'
               f'## Full Job Description\n{job.get("description", "Not retrieved")}\n')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:  # Never overwrite an unrelated existing lead.
        stream.write(content)
    if path.read_text() != content:
        raise ValueError("Lead readback mismatch")
    return path
