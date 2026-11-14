"""Keep upstream service outages visible without treating them as code failures."""
import json,re
from pathlib import Path

def availability_failures(report):
    failures=[(company,error.get('error','')) for company,result in report.get('sources',{}).items() for error in result.get('errors',[])]
    return failures if failures and all(re.fullmatch(r'Employer request failed: HTTP 5\d\d',message) for company,message in failures) else None

def check(path):
    report=json.loads(Path(path).read_text(encoding='utf-8'))
    failures=availability_failures(report)
    if failures is None:
        print('Collection failed for a reason requiring investigation. See collection-status.json.');return 1
    for company,message in failures:
        print(f'::warning title=Employer service unavailable::{company}: {message}. Previous check dates are retained; source health remains visible on the website.')
    print('Partial refresh completed. Employer availability errors remain in the published status report.')
    return 0

if __name__=='__main__':raise SystemExit(check('public/data/collection-status.json'))
