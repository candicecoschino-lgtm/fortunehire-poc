"""Recover separately labeled fields from already-verified adapter responses."""

import ast
import json
import re
from urllib.parse import parse_qs, unquote, urlsplit

from employer_adapters import Document


def matching_apple_record(body, requisition):
    records = []

    def walk(value, depth=0):
        if depth > 30:
            return
        if isinstance(value, dict):
            if 'jobNumber' in value:
                if value['jobNumber'] == requisition:
                    records.append(value)
            else:
                for child in value.values():
                    walk(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                walk(child, depth + 1)

    prefix = 'window.__staticRouterHydrationData = JSON.parse('
    for node in Document(body).nodes:
        if node['tag'] != 'script':
            continue
        script = ''.join(part for part in node['children'] if isinstance(part, str))
        if script.startswith(prefix):
            encoded, _ = json.JSONDecoder().raw_decode(script[len(prefix):])
            walk(json.loads(encoded))
    return records[0] if len(records) == 1 else None


def matching_oracle_record(body, requisition):
    value = json.loads(body)
    items = value.get('items') if isinstance(value, dict) else None
    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
        return None
    return items[0] if str(items[0].get('Id')) == requisition else None


def matching_phenom_job(body, requisition):
    matches = []
    for node in Document(body).nodes:
        if node['tag'] != 'script':
            continue
        script = ''.join(part for part in node['children'] if isinstance(part, str))
        assignment = re.search(r'\bphApp\.ddo\s*=\s*(?=\{)', script)
        if not assignment:
            continue
        try:
            payload, _ = json.JSONDecoder().raw_decode(script[assignment.end():])
            job = payload['jobDetail']['data']['job']
            identifier = job.get('reqId') or job.get('jobRequisitionId')
            if str(identifier) == requisition:
                matches.append(job)
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
    return matches[0] if len(matches) == 1 else None


def matching_cisco_description(body, requisition):
    job = matching_phenom_job(body, requisition)
    description = job.get('description') if job else None
    return description if isinstance(description, str) and description.strip() else None


def matching_taleo_record(body, requisition):
    history = Document(body).find('input', id='initialHistory')
    mapping = re.search(r'descRequisition:\s*\{\s*_size:\s*1,.*?_hlid:\s*(\[[^\]]+\])', body, re.S)
    if not history or not mapping:
        return None
    fields = ast.literal_eval(mapping[1])
    parts = history['attrs'].get('value', '').split('!|!')
    if (not isinstance(fields, list) or not all(isinstance(field, str) for field in fields)
            or len(set(fields)) != len(fields) or len(parts) < 3 + len(fields) or parts[2] != 'descRequisition'):
        return None
    values = {field: unquote(value).removeprefix('!*!').replace('\\:', ':')
              for field, value in zip(fields, parts[3:])}
    return values if values.get('reqlistitem.contestnumber') == requisition else None


def qualification_input(source, *, verified_body=None, source_url=None):
    """Keep employer qualification fields intact without editing feed adapters.

    Call only after the existing collector validates employer, URL and posting
    identity. `verified_body` is the same response used for normalization, not
    an independently fetched or unverified replacement. Pass the verified
    posting URL when the normalized source omits it.
    """
    result = dict(source)
    if not isinstance(verified_body, str):
        return result
    identifier = source.get('identifier')
    requisition = str((identifier.get('value') if isinstance(identifier, dict) else identifier) or '')
    url = urlsplit(source_url or source.get('url') or '')
    adapter = source.get('_adapter')
    if not requisition:
        return result
    try:
        if url.hostname == 'careers.cisco.com' and url.scheme == 'https':
            posting = re.match(r'^/global/en/job/(?:CISCISGLOBAL)?(\d+)(?:EXTERNALENGLOBAL)?(?:/|$)', url.path)
            if posting and posting[1] == requisition:
                description = matching_cisco_description(verified_body, requisition)
                if description:
                    result['description'] = description
        elif adapter == 'apple-public-location-posting' and url.hostname == 'jobs.apple.com':
            row = matching_apple_record(verified_body, requisition)
            if row:
                result.update({field: row[field] for field in ('minimumQualifications', 'preferredQualifications')
                               if field in row})
                result['description'] = [row.get('jobSummary'), row.get('description')]
                result['responsibilities'] = row.get('responsibilities')
        elif adapter == 'oracle-public-requisition-details' and url.path.rstrip('/').endswith('/' + requisition):
            row = matching_oracle_record(verified_body, requisition)
            if row:
                result['ExternalQualificationsStr'] = row.get('ExternalQualificationsStr')
                result['description'] = row.get('ExternalDescriptionStr')
                result['ExternalResponsibilitiesStr'] = row.get('ExternalResponsibilitiesStr')
        elif adapter == 'valero-public-taleo-display-data' and parse_qs(url.query).get('job') == [requisition]:
            row = matching_taleo_record(verified_body, requisition)
            if row:
                result['reqlistitem.qualification'] = row.get('reqlistitem.qualification')
                result['description'] = row.get('reqlistitem.description')
    except (ValueError, SyntaxError, TypeError):
        # Retain the verified normalized description when an optional original
        # field cannot be recovered exactly.
        return dict(source)
    return result
