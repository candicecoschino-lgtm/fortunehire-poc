"""Build the local resume prototype's sidecar from verified employer captures."""

import argparse
import json
from pathlib import Path
import re
from unicodedata import normalize
from urllib.parse import urlsplit

from qualification_extraction import extract_qualifications
from qualification_inputs import qualification_input


def qualification_record(job, source, verified_body=None, source_url=None):
    url = source_url or job['url']
    source = qualification_input(source, verified_body=verified_body, source_url=url)
    extracted = extract_qualifications(source, url, limit_per_kind=None)
    evidence = [{'kind': row.kind, 'text': row.text, 'types': list(row.types)}
                for row in extracted.evidence if row.kind in ('required', 'preferred')]
    return {'catalogSourceHash': job['sourceHash'], 'evidence': evidence}


def matching_records(jobs, records):
    return {job['id']: entry for job in jobs
            if job.get('status') == 'reviewed' and job.get('sourceHash')
            and isinstance(entry := records.get(job['id']), dict)
            and entry.get('catalogSourceHash') == job['sourceHash']
            and entry.get('evidence')}


def title_key(value):
    return ' '.join(normalize('NFKC', value).casefold().split())


def matches_posting(job, case):
    actual, captured = (urlsplit(item['url']) for item in (job, case))
    if (captured.scheme != 'https' or actual.hostname != captured.hostname
            or captured.username or captured.password
            or title_key(job['title']) != title_key(case['title'])):
        return False
    if (actual.path.rstrip('/').casefold() == captured.path.rstrip('/').casefold()
            and actual.query == captured.query):
        return True
    # Some employer URLs include a different slug for the same requisition.
    req = re.escape(str(job.get('requisitionId', '')).casefold())
    if not req:
        return False
    key = rf'(?<![\w-]){req}(?![\w-])'
    return all(re.search(key, url.path.casefold()) for url in (actual, captured))


def build(catalog, cases):
    jobs = {job['id']: job for job in catalog['jobs']}
    result = {}
    for case in cases:
        job = jobs.get(case['id'])
        if not job or not job.get('sourceHash') or not matches_posting(job, case):
            continue
        record = qualification_record(job, case['source'], case.get('verifiedBody'), case['url'])
        if record['evidence']:
            result[job['id']] = record
    return {'version': 1, 'jobs': result}


def main():
    root = Path(__file__).resolve().parents[1]
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('captures', type=Path, help='Verified local JSON with a cases array of id, title, url, and source')
    args.add_argument('--catalog', type=Path, default=root / 'public/data/jobs.json')
    args.add_argument('--output', type=Path, default=root / '.prototype-data/resume-qualifications.json')
    options = args.parse_args()
    source = json.loads(options.captures.read_text(encoding='utf-8'))
    catalog = json.loads(options.catalog.read_text(encoding='utf-8'))
    sidecar = build(catalog, source['cases'])
    options.output.parent.mkdir(parents=True, exist_ok=True)
    staging = options.output.with_suffix('.tmp')
    staging.write_text(json.dumps(sidecar, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    staging.replace(options.output)
    print(f"Qualification evidence for {len(sidecar['jobs'])} catalog postings")


if __name__ == '__main__':
    main()
