"""Small local persistence and arithmetic helpers; no search or model judgment."""
import json
import math
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
from fractions import Fraction
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


def number(value, upper, name):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= upper:
        raise ValueError("Invalid " + name)
    return Fraction(str(value))


def validate_weights(weights):
    names = {"required", "preferred", "domain", "trajectory", "scope", "company"}
    if not isinstance(weights, dict) or set(weights) != names:
        raise ValueError("Specify all six rubric weights")
    values = {k: number(v, 100, k) for k, v in weights.items()}
    if sum(values.values()) != 100 or values["required"] + values["domain"] <= 0:
        raise ValueError("Weights must total100 with a positive required/domain block")
    return values


def validated_score(breakdown, weights):
    """Check fit-v2 arithmetic; caller supplies the reviewed settings weights."""
    w = validate_weights(weights)
    if "weights" in breakdown and breakdown["weights"] != weights:
        raise ValueError("Receipt weights differ from the reviewed settings")
    if breakdown.get("rubric_version") != "fit-v2" or "C" in breakdown or breakdown.get("domain_adjustment", 0) != 0:
        raise ValueError("Use fit-v2 components; legacy scores/adjustments cannot be reinterpreted")
    ratings = {name: number(breakdown[name], upper, name)
               for name, upper in (("A", 50), ("D", 15), ("T", 10), ("S", 10), ("K", 5))}
    status = breakdown["preferred_status"]
    if status not in ("present", "absent", "unknown") or type(breakdown["full_jd"]) is not bool:
        raise ValueError("Record preferred status and full-JD evidence explicitly")
    if status == "absent" and not breakdown["full_jd"]:
        raise ValueError("Incomplete evidence cannot establish absent preferences")
    if status == "present":
        preferred = number(breakdown["B"], 25, "B")
    else:
        if breakdown["B"] is not None:
            raise ValueError("Absent or unknown preferences use B=null, not neutral/free points")
        preferred = Fraction(0)
    deductions = breakdown["deductions"]
    if not isinstance(deductions, list):
        raise ValueError("Deductions must be a list")
    for item in deductions:
        if not isinstance(item, dict) or type(item.get("points")) is not int or item["points"] not in (3, 20) or not item.get("clause") or not item.get("evidence"):
            raise ValueError("Unsupported deduction or missing evidence")
    if breakdown["A"] != max(0, 50 - sum(x["points"] for x in deductions)):
        raise ValueError("Required-score arithmetic mismatch")
    cap = breakdown.get("cap")
    cap = number(cap, 100, "cap") if cap is not None else Fraction(100)
    if not breakdown["full_jd"] or status == "unknown":
        cap = min(cap, 60)
    fit = w["required"] * ratings["A"] / 50 + w["domain"] * ratings["D"] / 15
    if status == "absent":
        fit *= (w["required"] + w["preferred"] + w["domain"]) / (w["required"] + w["domain"])
    total = fit + w["preferred"] * preferred / 25
    total += w["trajectory"] * ratings["T"] / 10 + w["scope"] * ratings["S"] / 10 + w["company"] * ratings["K"] / 5
    return float(min(total, cap))


def write_lead(workspace, job, breakdown):
    """Caller holds the lock and verifies gates/dedup; receipts retain the calculation."""
    settings = json.loads((Path(workspace) / "Instructions/settings.json").read_text())
    threshold = settings["review_threshold"]
    score = validated_score(breakdown, settings["weights"]) if breakdown is not None else None
    folder = "Yes" if score is None or score >= threshold else "No"
    if breakdown is not None and breakdown["A"] <= 15:
        folder = "No"
    if job.get("priority") == "Apply" and (score is None or folder != "Yes" or not breakdown["full_jd"] or breakdown["preferred_status"] == "unknown"):
        raise ValueError("Ineligible Apply disposition")
    label = re.sub(r'[^\w .()-]', "_", job["company"] + " - " + job["title"]).strip(". ")[:160]
    if not label:
        raise ValueError("Missing role label")
    # Keep precision for decisions; display truncation cannot promote a boundary score.
    shown = format(Decimal(str(score)).quantize(Decimal("0.01"), rounding=ROUND_FLOOR), "f").rstrip("0").rstrip(".") if score is not None else "Unscored"
    filename = (shown + ". " if score is not None else "Manual Check - ") + label + ".md"
    path = Path(workspace) / "Leads" / folder / filename
    content = (f'# {job["title"]} @ {job["company"]}\n\n'
               f'**Score:** {shown}\n'
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
