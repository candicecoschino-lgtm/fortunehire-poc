"""Compare populated fields and reviewer-labeled evidence in offline case files."""

import argparse
from collections import Counter, defaultdict
from html import unescape
import json
from pathlib import Path

from qualification_extraction import KINDS, LIST_ITEM, extract_qualifications


def wording(text):
    """Ignore only list markers and whitespace when comparing complete evidence."""
    return ' '.join(LIST_ITEM.sub('', unescape(text)).split())


def score(evidence, reference):
    """Compare complete statements in the correct bucket, counting omissions."""
    terms = Counter()
    matched, covered = set(), set()
    canonical = [(item['kind'], wording(item['text'])) for item in reference]
    for kind, text in evidence:
        text = wording(text)
        terms['emitted'] += 1
        same = [index for index, (_, original) in enumerate(canonical) if text == original]
        correct = [index for index in same if canonical[index][0] == kind and index not in matched]
        if correct:
            matched.add(correct[0])
            covered.add(kind)
            terms['correct'] += 1
        elif any(canonical[index][0] != kind for index in same):
            terms['wrong_bucket'] += 1
        elif same:
            terms['duplicate'] += 1
        elif len(text) >= 12 and any(text in original or original in text for _, original in canonical):
            terms['wording_difference'] += 1
        else:
            terms['unsupported'] += 1
    for index, (kind, _) in enumerate(canonical):
        terms[f'{kind}_source_statements'] += 1
        if index not in matched:
            terms[f'{kind}_missing'] += 1
    for kind in KINDS:
        if any(expected_kind == kind for expected_kind, _ in canonical):
            terms[f'{kind}_source_jobs'] += 1
        if kind in covered:
            terms[f'{kind}_correct_jobs'] += 1
    return terms


def audit(cases, references):
    before_keys = {'required': 'requiredSkills', 'preferred': 'preferredSkills'}
    counts = defaultdict(Counter)
    accuracy = defaultdict(lambda: {'before': Counter(), 'after': Counter()})
    for case in cases:
        if not (case.get('sameHash') and case.get('sameContext')):
            continue
        employer = case['employer']
        result = extract_qualifications(case['source'], case['url'])
        old = [(kind, text) for kind, key in before_keys.items() for text in case['before'].get(key, [])]
        new = [(item.kind, item.text) for item in result.evidence]
        reference = references.get(case['id'])
        for key in (employer, 'all'):
            row = counts[key]
            row['jobs'] += 1
            for kind in KINDS:
                row[f'before_{kind}'] += any(label == kind for label, _ in old)
                row[f'after_{kind}'] += any(label == kind for label, _ in new)
                row[f'output_limit_{kind}'] += result.omitted[kind]
            if reference is not None:
                row['reviewed_jobs'] += 1
                accuracy[key]['before'].update(score(old, reference))
                accuracy[key]['after'].update(score(new, reference))
    return {'coverage': dict(counts), 'reviewed_accuracy': dict(accuracy)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case_files', type=Path, nargs='+')
    parser.add_argument('--references', type=Path, help='Local JSON map from job ID to reviewed kind/text statements')
    args = parser.parse_args()
    cases = {}
    for file in args.case_files:
        for case in json.loads(file.read_text(encoding='utf-8')):
            if case.get('sameHash') and case.get('sameContext'):
                cases[case['id']] = case
    references = json.loads(args.references.read_text(encoding='utf-8')) if args.references else {}
    print(json.dumps(audit(cases.values(), references), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
