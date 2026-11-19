"""Synthetic role descriptions; never published as company data."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from function_context import extract_function_context
from collect_jobs import normalize_posting
from test_collector import body, URL, NOW


class FunctionContextTests(unittest.TestCase):
    def test_only_duties_not_benefits_qualifications_or_company_profile(self):
        text='''About us
You will provide customer support across our global brand.
Responsibilities:
Build databases for the sales reporting team.
Develop software to automate reports.
Required qualifications:
You will manage employee relations in a prior role.
Benefits:
Manage employee benefits and provide medical care.
'''
        context=extract_function_context(text,{'occupationalCategory':'Information Technology'})
        self.assertEqual(context['duties'],['Build databases for the sales reporting team.','Develop software to automate reports.'])
        self.assertEqual(context['category'],'Information Technology')

    def test_explicit_role_sentence_without_a_heading_and_inline_headings(self):
        for text in ['You will process payroll for employees.','Responsibilities: Process payroll for employees.','In this role: Process payroll for employees.']:
            self.assertEqual(len(extract_function_context(text)['duties']),1,text)
        self.assertEqual(extract_function_context('We develop software. Our company sells insurance.')['duties'],[])

    def test_existing_role_sections_capture_more_specific_action_verbs(self):
        text='''Key Responsibilities:
Collaborate with platform teams to integrate enterprise systems.
Reconcile financial activity and draft customer-facing reports.
Configure Linux infrastructure and troubleshoot network services.
Required Skills:
Python
Benefits:
Manage employee benefits and provide medical care.
'''
        context=extract_function_context(text)
        self.assertEqual(context['duties'],[
            'Collaborate with platform teams to integrate enterprise systems.',
            'Reconcile financial activity and draft customer-facing reports.',
            'Configure Linux infrastructure and troubleshoot network services.'
        ])
        self.assertEqual(context['requiredSkills'],['Python'])

    def test_bounded_deduplicated_and_bad_categories(self):
        lines=['Responsibilities']+[f'Build software for product number {i}.' for i in range(30)]
        context=extract_function_context('\n'.join(lines),{'department':{'name':'Engineering'}})
        self.assertEqual(len(context['duties']),16)
        self.assertEqual(context['category'],'Engineering')
        self.assertEqual(extract_function_context('Responsibilities\nBuild software for product teams.\nBuild software for product teams.')['duties'],['Build software for product teams.'])
        self.assertEqual(extract_function_context('',{'occupationalCategory':['invalid']})['category'],'')

    def test_excludes_education_pay_benefits_schedule_and_location_sections(self):
        text='''Responsibilities:
Develop software applications for clinical workflows.
Coordinate implementation with engineering teams.
Required Skills:
Python
SQL
Minimum Education/Experience Requirement:
Bachelor's degree in computer science is required.
Pay Transparency:
The salary range for this role is $90,000 to $120,000.
Benefits:
Manage employee benefits and administer medical coverage.
Schedule:
Work 40 hours per week on the night shift.
Location:
Hybrid in Detroit, Michigan.
'''
        context=extract_function_context(text)
        self.assertEqual(context['duties'],[
            'Develop software applications for clinical workflows.',
            'Coordinate implementation with engineering teams.'
        ])
        self.assertEqual(context['requiredSkills'],['Python','SQL'])

    def test_excludes_noise_even_when_embedded_in_skills_lines(self):
        context=extract_function_context('''Required Qualifications:
Python
Bachelor's degree required
Minimum 2 years relevant experience in shipping and inventory control
Salary range $70,000 to $90,000
Night shift schedule
Work location: Detroit
''')
        self.assertEqual(context['requiredSkills'],['Python'])

    def test_collector_carries_only_isolated_description_and_refresh_replaces_evidence(self):
        html='<h2>Responsibilities</h2><ul><li>Build databases for sales reporting.</li></ul><h2>Benefits</h2><p>We offer health insurance.</p>'
        job=normalize_posting(body(description=html),URL,'boeing',NOW)
        self.assertEqual(job['functionContext']['duties'],['Build databases for sales reporting.'])
        changed=normalize_posting(body(description='<p>You will process payroll for employees.</p>'),URL,'boeing',NOW)
        self.assertEqual(changed['id'],job['id'])
        self.assertEqual(changed['functionContext']['duties'],['You will process payroll for employees.'])
        self.assertNotEqual(changed['sourceHash'],job['sourceHash'])
