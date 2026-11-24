"""Qualification evidence regression tests using synthetic employer records."""

from pathlib import Path
import json
import sys
import unittest
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from qualification_extraction import extract_qualifications
from qualification_inputs import qualification_input
from audit_qualifications import score
from function_context import extract_function_context


URL = 'https://careers.example.com/jobs/123'


class QualificationExtractionTests(unittest.TestCase):
    def test_position_invariant_after_sixteen_duties_and_past_100000_characters(self):
        qualifications = '''
        <h4>Minimum Qualifications...</h4>
        <ul><li>Bachelor’s degree or four years of equivalent professional experience.</li></ul>
        <h5>Additional Preferred Qualifications</h5>
        <ul><li>PMP certification or comparable credential.</li></ul>
        '''
        duty_lines = [f'Build financial reporting workflows for department {i}.' for i in range(40)]
        duties = '<h3>Responsibilities</h3>' + ''.join(f'<p>{line}</p>' for line in duty_lines)
        padding = '<p>' + 'Report details. ' * 8000 + '</p>'
        before = extract_qualifications({'description': qualifications + duties}, URL)
        after = extract_qualifications({'description': duties + padding + qualifications}, URL)
        self.assertEqual([(item.kind, item.text) for item in before.evidence],
                         [(item.kind, item.text) for item in after.evidence])
        self.assertEqual([item.kind for item in after.evidence], ['required', 'preferred'])
        self.assertEqual(after.evidence[0].types, ('education', 'experience'))
        self.assertGreater(after.evidence[0].block, 40)
        legacy = extract_function_context('\n'.join(['Responsibilities', *duty_lines, 'Required Qualifications', 'SQL']))
        self.assertEqual((len(legacy['duties']), legacy['requiredSkills']), (16, []))

    def test_heading_variants_and_classification(self):
        text = '''
        Basic Qualifications (Required Skills and Experience):
        5+ years of relevant experience in data analytics.
        Preferred Qualifications (Desired Skills/Experience)
        SQL or Python proficiency.
        Ｄｅｓｉｒｅｄ Qualifications
        Bonus points:
        Experience working on public-sector projects.
        Qualifications/Requirements：
        Strong communication skills.
        Workday experience preferred.
        Must hold an active North Carolina pharmacist license.
        Optional Qualifications
        Experience working with Kubernetes.
        '''
        result = extract_qualifications({'description': text}, URL)
        self.assertEqual([q.kind for q in result.evidence],
                         ['required', 'preferred', 'preferred', 'ambiguous', 'preferred', 'required', 'preferred'])
        self.assertEqual(result.evidence[3].confidence, 'medium')
        self.assertEqual(result.evidence[5].types, ('license',))

    def test_keeps_whole_bullets_alternatives_and_proficiency_lead_in(self):
        result = extract_qualifications({'description': '''
            <h4>Required Qualifications</h4><ul>
            <li><p>BS in computer science, engineering, or a related field</p>
              <p>or equivalent professional experience.</p></li>
            <li>Three years of experience in SQL, Python, or R.</li></ul>
            <p>Demonstrated proficiency in:</p><ul><li>Terraform</li></ul>
        '''}, URL)
        self.assertEqual([q.text for q in result.evidence], [
            'BS in computer science, engineering, or a related field or equivalent professional experience.',
            'Three years of experience in SQL, Python, or R.',
            'Demonstrated proficiency in: Terraform',
        ])
        self.assertTrue(all(q.section == 'Required Qualifications' and q.source_url == URL for q in result.evidence))

    def test_nested_proficiency_label_does_not_bleed_into_sibling_requirements(self):
        result = extract_qualifications({'description': '''
            <h3>Required Qualifications</h3><ul>
            <li>Demonstrated proficiency in:<ul><li>SQL</li><li>Python</li></ul></li>
            <li>Experience in operations, including manufacturing, or equivalent experience.</li>
            </ul>
        '''}, URL)
        self.assertEqual([q.text for q in result.evidence], [
            'Demonstrated proficiency in: SQL', 'Demonstrated proficiency in: Python',
            'Experience in operations, including manufacturing, or equivalent experience.',
        ])

    def test_report_distinguishes_wrong_bucket_wording_loss_and_unsupported_text(self):
        report = score([
            ('preferred', 'Degree or equivalent experience.'),
            ('required', 'PMP certification'),
            ('required', 'Paid time off'),
        ], [
            {'kind': 'required', 'text': 'Degree or equivalent experience.'},
            {'kind': 'required', 'text': 'PMP certification or comparable credential.'},
        ])
        self.assertEqual([report[key] for key in ('wrong_bucket', 'wording_difference', 'unsupported', 'required_missing')],
                         [1, 1, 1, 2])

    def test_nonqualification_sections_and_unrelated_prose_are_rejected(self):
        result = extract_qualifications({'description': '''
            Company Overview
            Our teams have extensive experience in training and operations.
            Responsibilities
            Must lead the recruitment team.
            Build software applications with SQL.
            Required Qualifications: Experience in SQL application development.
            Develop dashboards and manage engineers.
            Our company is an equal opportunity employer.
            Benefits:
            Tuition assistance is required for enrollment.
            Travel Requirements
            Travel may be required.
            How to apply
            A background check is required to use the application website.
            Additional Preferred Qualifications
            Experience presenting results to executives.
        '''}, URL)
        self.assertEqual([q.text for q in result.evidence],
                         ['Experience in SQL application development.', 'Experience presenting results to executives.'])

    def test_dedicated_fields_supply_evidence_and_outrank_duplicate_body_labels(self):
        result = extract_qualifications({
            'minimumQualifications': ['Terraform', 'Bachelor’s degree or equivalent work experience.'],
            'preferredQualifications': '<ul><li>PMP certification.</li></ul>',
            'description': '<h5>Preferred</h5><p>Terraform.</p><p>Experience with Azure.</p>',
        }, URL)
        self.assertEqual([(q.text, q.kind, q.source_field) for q in result.evidence], [
            ('Terraform', 'required', 'minimumQualifications'),
            ('Bachelor’s degree or equivalent work experience.', 'required', 'minimumQualifications'),
            ('PMP certification.', 'preferred', 'preferredQualifications'),
            ('Experience with Azure.', 'preferred', 'description'),
        ])

    def test_conflicting_dedicated_fields_remain_ambiguous(self):
        result = extract_qualifications({
            'minimumQualifications': 'SQL', 'preferredQualifications': 'SQL',
            'description': 'Required Skills: SQL',
        }, URL)
        self.assertEqual([(q.kind, q.confidence) for q in result.evidence], [('ambiguous', 'medium')])

    def test_independent_storage_limits_and_no_fragment_truncation(self):
        long_statement = 'Experience with ' + 'complex regulated systems and workflows, ' * 18 + 'or equivalent experience.'
        result = extract_qualifications({
            'description': 'Minimum Requirements\n' + long_statement + '\nExperience with Excel.\n'
                           'Nice to have\nExperience with Tableau.\nExperience in SaaS.',
        }, URL, limit_per_kind=1)
        self.assertEqual([q.text for q in result.evidence], [long_statement, 'Experience with Tableau.'])
        self.assertEqual(result.omitted, {'required': 1, 'preferred': 1, 'ambiguous': 0})

    def test_nested_sections_do_not_pull_in_script_content(self):
        source = {'description': '&lt;h6&gt;Minimum Requirements&lt;/h6&gt;'
                                 '&lt;script&gt;voicemail credential required&lt;/script&gt;'
                                 '&lt;p&gt;SQL proficiency and HIPAA knowledge.&lt;/p&gt;'}
        result = extract_qualifications(source, URL)
        self.assertEqual([q.text for q in result.evidence], ['SQL proficiency and HIPAA knowledge.'])

    def test_only_valid_https_application_urls_are_allowed_for_provenance(self):
        for invalid in ('ftp://career.example/x', 'https://', 'https://user:password@example.com'):
            with self.subTest(url=invalid), self.assertRaises(ValueError):
                extract_qualifications({}, invalid)


    def test_preferred_credential_heading_after_required_remains_preferred(self):
        result = extract_qualifications({'description': '''
            Required Qualifications
            Five years of experience in pharmacy operations.
            Preferred Certifications:
            Certified pharmacy technician credential.
            Preferred Experience:
            Experience with robotics and workflow automation.
        '''}, URL)
        self.assertEqual([(item.kind, item.text) for item in result.evidence], [
            ('required', 'Five years of experience in pharmacy operations.'),
            ('preferred', 'Certified pharmacy technician credential.'),
            ('preferred', 'Experience with robotics and workflow automation.'),
        ])

    def test_required_license_section_and_explicit_outside_requirement(self):
        result = extract_qualifications({'description': '''
            Minimum Licenses
            Active Pennsylvania pharmacist license.
            Must maintain nonresident pharmacist licensure where required.
            Responsibilities
            Coordinate medicine fulfillment.
            Must hold an active resident-state pharmacist license.
        '''}, URL)
        self.assertEqual([(item.kind, item.text) for item in result.evidence], [
            ('required', 'Active Pennsylvania pharmacist license.'),
            ('required', 'Must maintain nonresident pharmacist licensure where required.'),
            ('required', 'Must hold an active resident-state pharmacist license.'),
        ])

    def test_dash_delimited_preferred_heading_does_not_inherit_required(self):
        result = extract_qualifications({'description': '''
            Required Qualifications - Three years of experience in healthcare operations.
            Desired Experience - Experience with inventory management systems.
        '''}, URL)
        self.assertEqual([(item.kind, item.text) for item in result.evidence], [
            ('required', 'Three years of experience in healthcare operations.'),
            ('preferred', 'Experience with inventory management systems.'),
        ])



class QualificationInputTests(unittest.TestCase):
    def test_apple_uses_matched_dedicated_fields(self):
        url = 'https://jobs.apple.com/en-us/details/123-5/example'
        verified = {'identifier': '123-5', 'url': url, '_adapter': 'apple-public-location-posting', 'description': 'Original'}
        row = {'jobNumber': '123-5', 'jobSummary': 'Summary', 'description': 'Role',
               'minimumQualifications': 'SQL', 'preferredQualifications': 'Python'}
        body = '<script>window.__staticRouterHydrationData = JSON.parse(' + json.dumps(json.dumps({'loaderData': row})) + ');</script>'
        result = extract_qualifications(qualification_input(verified, verified_body=body), url)
        self.assertEqual([(e.text, e.kind) for e in result.evidence], [('SQL', 'required'), ('Python', 'preferred')])
        self.assertEqual(verified['description'], 'Original')
        self.assertEqual(qualification_input({**verified, 'identifier': 'wrong'}, verified_body=body)['description'], 'Original')

    def test_oracle_retains_qualified_scope_without_using_responsibilities(self):
        url = 'https://careers.oracle.com/en/sites/CX/job/123'
        verified = {'identifier': '123', 'url': url, '_adapter': 'oracle-public-requisition-details'}
        body = json.dumps({'items': [{'Id': 123, 'ExternalDescriptionStr': '<p>Role at Oracle</p>',
                           'ExternalQualificationsStr': '<p>Certification in cloud security.</p>',
                           'ExternalResponsibilitiesStr': '<p>Support cloud security systems.</p>'}]})
        result = extract_qualifications(qualification_input(verified, verified_body=body), url)
        self.assertEqual([(q.kind, q.source_field) for q in result.evidence], [('ambiguous', 'ExternalQualificationsStr')])
        self.assertEqual(result.evidence[0].types, ('certification',))

    def test_taleo_prefers_matched_public_qualification_entry(self):
        url = 'https://example.taleo.net/careersection/2/jobdetail.ftl?job=123'
        fields = ['reqlistitem.contestnumber', 'reqlistitem.description', 'reqlistitem.qualification']
        history = '!|!'.join(['x', 'x', 'descRequisition', '123', quote('Role description'),
                              quote('Required qualifications: Excel proficiency.')])
        body = f'<input id="initialHistory" value="{history}"><script>descRequisition: {{ _size: 1,_hlid: {fields}}}</script>'
        source = {'identifier': '123', 'url': url, '_adapter': 'valero-public-taleo-display-data'}
        result = extract_qualifications(qualification_input(source, verified_body=body), url)
        self.assertEqual([(e.text, e.kind, e.source_field) for e in result.evidence],
                         [('Excel proficiency.', 'required', 'reqlistitem.qualification')])


if __name__ == '__main__':
    unittest.main()
