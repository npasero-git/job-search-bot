"""Bounded public ATS fetch utilities. Source contracts live in companies.json.

No endpoint discovery, scoring, credential use or browser access. Callers persist
query/page cursors after each response, before moving to the next work unit.
"""
import json
import subprocess
import hashlib
import re
from pathlib import Path
from urllib.parse import urlsplit


def fetch(url, body=None):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise ValueError("Public HTTPS source required")
    args = ["curl", "--silent", "--show-error", "--max-time", "30",
            "--proto", "=https", "-w", "\n%{http_code}",
            "-H", "Accept: application/json", "-H", "Cache-Control: no-cache, no-store",
            "-H", "Pragma: no-cache"]
    if body is not None:
        args += ["-X", "POST", "-H", "Content-Type: application/json", "-d", json.dumps(body)]
    try:
        result = subprocess.run(args + [url], capture_output=True, text=True, timeout=40)
    except subprocess.TimeoutExpired:
        return {"ok": False, "status": "", "error": "timeout"}
    raw, _, status = result.stdout.rpartition("\n")
    if result.returncode or status != "200":
        return {"ok": False, "status": status, "error": "timeout" if result.returncode == 28
                else "curl_failed" if result.returncode else "http_" + status}
    try:
        return {"ok": True, "status": status, "data": json.loads(raw)}
    except ValueError:
        return {"ok": False, "status": status, "error": "invalid_json"}


def list_request(config, query="Product Manager", offset=0):
    provider = config["provider"]
    if provider == "workday":
        cap = min(3, max(1, int(config.get("pagination_max_pages", 1))))
        if offset not in range(0, cap * 20, 20):
            raise ValueError("Unapproved Workday offset")
        url = f'https://{config["host"]}/wday/cxs/{config["tenant"]}/{config["site"]}/jobs'
        return url, {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": query}
    if provider == "greenhouse":
        return f'https://boards-api.greenhouse.io/v1/boards/{config["slug"]}/jobs?content=true', None
    if provider == "ashby":
        return f'https://api.ashbyhq.com/posting-api/job-board/{config["slug"]}', None
    if provider == "lever":
        return f'https://api.lever.co/v0/postings/{config["slug"]}?mode=json', None
    raise ValueError("Custom/iCIMS: follow the persisted company-specific contract, not a guessed endpoint")


def workday_page(data, prior_ids, first_total=None):
    jobs, total = data.get("jobPostings"), data.get("total")
    if not isinstance(jobs, list) or type(total) is not int or total < 0:
        raise ValueError("Malformed Workday result")
    expected = total if first_total is None else first_total
    if first_total is not None and total not in (0, first_total):
        raise ValueError("Workday count changed")
    if any(not isinstance(j, dict) or not isinstance(j.get('title'), str) for j in jobs):
        raise ValueError("Malformed Workday job")
    ids = [j.get("externalPath") for j in jobs]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)) or set(ids) & set(prior_ids):
        raise ValueError("Workday duplicate/invalid page")
    count = len(prior_ids) + len(ids)
    if count > expected:
        raise ValueError("Workday count exceeded")
    complete = bool(expected) and count == expected
    return {"ids": ids, "first_total": expected, "complete": complete,
            "reason": None if complete else "empty_or_cache" if expected == 0
            else "premature_end" if len(jobs) != 20 else "remaining_or_page_cap"}


def workday_queries(company):
    queries = ["Product Manager", "Product Management", "Senior Product Manager",
               "Technical Product Manager", "Principal Product Manager", "AI Product Manager"]
    if str(company.get('category', '')).lower() == 'semiconductor':
        queries += ["Product Line Manager", "Product Marketing Engineer"]
    return queries


def greenhouse_date(job):
    """Publication wins over updates; return the provenance with the value."""
    for field in ('first_published_at', 'updated_at'):
        if job.get(field):
            return job[field], field
    return None, 'unknown'


def source_enabled(company, config):
    return company.get('active') is not False and config.get('active') is not False


def workday_id(job):
    """Preserve the existing local req convention; also retain the full source URL."""
    path = job.get('externalPath', '')
    match = re.search(r'_([A-Za-z0-9]+)(?:-\d+)?$', path)
    return match.group(1) if match else path


def source_key(config):
    provider = config['provider']
    fields = ('host', 'tenant', 'site') if provider == 'workday' else ('slug',) if provider in ('greenhouse', 'ashby', 'lever') else ('endpoint', 'type', 'fetch_method')
    return provider + ':' + json.dumps({k: config.get(k) for k in fields}, sort_keys=True, separators=(',', ':'))


def save_response(directory, run_id, config, request, data):
    """Immutable, source-bound raw response; never key evidence by company display name."""
    record = {'source_key': source_key(config), 'request': request, 'data': data}
    raw = json.dumps(record, ensure_ascii=False, sort_keys=True).encode()
    identity = hashlib.sha256((run_id + source_key(config) + json.dumps(request, sort_keys=True)).encode()).hexdigest()
    path = Path(directory) / (identity + '-' + hashlib.sha256(raw).hexdigest()[:16] + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Conflicting source cache')
    else:
        with path.open('xb') as stream:
            stream.write(raw)
    return str(path)


def read_response(path, config):
    record = json.loads(Path(path).read_text())
    if record['source_key'] != source_key(config):
        raise ValueError('Source identity mismatch')
    return record['data']


def workday_company(company, config, fetcher=fetch, cache_dir=None, run_id='run', prior=None):
    """One company, all required variants, unchanged per-query caps; reusable locally/cloud."""
    from copy import deepcopy
    if not source_enabled(company, config):
        return {'source_key': source_key(config), 'variants': {}, 'jobs': [],
                'evidence': [], 'complete': False, 'skipped': 'inactive'}
    result = deepcopy(prior) if prior else {'source_key': source_key(config), 'variants': {}, 'jobs': [], 'evidence': []}
    if result['source_key'] != source_key(config):
        raise ValueError('Wrong company checkpoint')
    cap = min(3, max(1, int(config.get('pagination_max_pages') or 1)))
    seen = {j['externalPath'] for j in result['jobs']}
    for query in workday_queries(company):
        if result['variants'].get(query, {}).get('attempt_finished'):
            continue
        stats = result['variants'].setdefault(query, {'pages': 0, 'ids': [], 'total_reported': None, 'complete': False})
        for page in range(stats['pages'], cap):
            url, body = list_request(config, query, page * 20)
            response = fetcher(url, body)
            stats['pages'] += 1
            if not response['ok']:
                stats['incomplete_reason'] = response['error']
                break
            data = response['data']
            if cache_dir:
                result['evidence'].append(save_response(cache_dir, run_id, config, body, data))
            try:
                parsed = workday_page(data, stats['ids'], stats['total_reported'])
            except (ValueError, AttributeError) as exc:
                stats['incomplete_reason'] = str(exc)
                break
            stats['ids'] += parsed['ids']
            stats['total_reported'] = parsed['first_total']
            stats['complete'] = parsed['complete']
            stats['incomplete_reason'] = parsed['reason']
            for job in data['jobPostings']:
                if job['externalPath'] not in seen:
                    seen.add(job['externalPath'])
                    result['jobs'].append(job)
            if parsed['complete'] or parsed['reason'] != 'remaining_or_page_cap':
                break
        stats['attempt_finished'] = True
        stats['unique_records'] = len(stats['ids'])
        if stats.get('incomplete_reason') == 'remaining_or_page_cap':
            stats['incomplete_reason'] = 'page_cap'
    result['complete'] = all(result['variants'][q]['complete'] for q in workday_queries(company))
    return result
