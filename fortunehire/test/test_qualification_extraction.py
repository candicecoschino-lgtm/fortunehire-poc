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

    def test_dedicated_fields_supply_evidence_and_conflicting_body_labels_stay_ambiguous(self):
        result = extract_qualifications({
            'minimumQualifications': ['Terraform', 'Bachelor’s degree or equivalent work experience.'],
            'preferredQualifications': '<ul><li>PMP certification.</li></ul>',
            'description': '<h5>Preferred</h5><p>Terraform.</p><p>Experience with Azure.</p>',
        }, URL)
        self.assertEqual([(q.text, q.kind, q.source_field) for q in result.evidence], [
            ('Terraform', 'ambiguous', 'minimumQualifications'),
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

    def assert_statements(self, source, expected):
        result = extract_qualifications(source, URL)
        self.assertEqual([(item.kind, item.text) for item in result.evidence], expected)
        return result

    def test_cencora_pharmacist_keeps_state_and_business_need_conditions(self):
        self.assert_statements({'description': '''
            <p>Responsibilities:</p>
            <p>1. Maintain records of state licenses and certifications.<br>
            2. Maintains active pharmacist license in home state and obtains/maintains required
            non-resident state licenses as business needs dictate to support multi-state operations.<br>
            3. Requires Pennsylvania active pharmacist license.</p>
            <p>Education:</p>
            <p>Requires a Degree in Pharmacy from an accredited College of Pharmacy.
            Unrestricted, current state license as a Registered Pharmacist in resident state is required.
            New Graduates are encouraged to apply.</p>
        '''}, [
            ('required', 'Maintains active pharmacist license in home state and obtains/maintains required '
                         'non-resident state licenses as business needs dictate to support multi-state operations.'),
            ('required', 'Requires Pennsylvania active pharmacist license.'),
            ('required', 'Requires a Degree in Pharmacy from an accredited College of Pharmacy.'),
            ('required', 'Unrestricted, current state license as a Registered Pharmacist in resident state is required.'),
        ])

    def test_soft_skills_reset_strength_and_explicit_degree_preference_wins(self):
        self.assert_statements({'description': '''
            <p>Minimum Qualifications</p>
            <p>Juris Doctor degree preferred, or equivalent compliance experience.</p>
            <p>Preferred Qualifications</p>
            <p>Experience presenting to agency staff.</p>
            <p>Soft Skills:</p>
            <ul><li>Ability to work independently.</li><li>Strong communication skills.</li></ul>
        '''}, [
            ('preferred', 'Juris Doctor degree preferred, or equivalent compliance experience.'),
            ('preferred', 'Experience presenting to agency staff.'),
            ('ambiguous', 'Ability to work independently.'),
            ('ambiguous', 'Strong communication skills.'),
        ])

    def test_typical_tenure_is_ambiguous_and_a_wrapped_preference_is_complete(self):
        self.assert_statements({'description': '''
            <p>Education:</p>
            <ul>
                <li>Normally requires a minimum of two years of pharmacy experience.
                Technician certification from a national</li>
                <li>certification provider or another comparable credential is preferred.</li>
                <li>An active technician or trainee license is required.
                For further information, please consult the state board.</li>
            </ul>
        '''}, [
            ('ambiguous', 'Normally requires a minimum of two years of pharmacy experience.'),
            ('preferred', 'Technician certification from a national certification provider or another '
                          'comparable credential is preferred.'),
            ('required', 'An active technician or trainee license is required.'),
        ])

    def test_topical_sections_read_strength_labels_and_keep_or_clause(self):
        self.assert_statements({'description': '''
            <p>Responsibilities:</p><p>Prepare billing records.</p>
            <p>Education and Work Experience</p>
            <ul>
                <li>Requires broad training in accounting, generally obtained through an associate degree.</li>
                <li>Minimum 5 years of accounting software experience.</li>
                <li>Must have advanced Excel skills. Writing formulas and pivot tables.</li>
            </ul>
            <p>Education/Experience:</p>
            <p>Required A High School diploma</p><p>Required or equivalent work experience</p>
            <p>Preferred A Bachelor's Degree in a related field</p>
            <p>Candidate Experience: Required 2+ years of outreach experience</p>
            <p>Required 4+ years of experience in Event Planning</p>
        '''}, [
            ('required', 'Requires broad training in accounting, generally obtained through an associate degree.'),
            ('required', 'Minimum 5 years of accounting software experience.'),
            ('required', 'Must have advanced Excel skills. Writing formulas and pivot tables.'),
            ('required', 'Required A High School diploma Required or equivalent work experience'),
            ('preferred', "Preferred A Bachelor's Degree in a related field"),
            ('required', 'Candidate Experience: Required 2+ years of outreach experience'),
            ('required', 'Required 4+ years of experience in Event Planning'),
        ])

    def test_timed_credentials_and_license_conditions_keep_their_complete_wording(self):
        self.assert_statements({'description': '''
            <p>Work Experience</p>
            <ul>
                <li>Candidates must be willing to obtain a Pharmacy Operations (PO) credential within six months.</li>
                <li>An active state license is required. If you live outside the state, a second license is required.</li>
                <li>Experience with medical billing helpful.</li>
                <li>Requires computer skills. A current driver's license is required.</li>
            </ul>
        '''}, [
            ('required', 'Candidates must be willing to obtain a Pharmacy Operations (PO) credential within six months.'),
            ('required', 'An active state license is required. If you live outside the state, a second license is required.'),
            ('preferred', 'Experience with medical billing helpful.'),
            ('required', 'Requires computer skills.'),
            ('required', "A current driver's license is required."),
        ])

    def test_nested_travel_addresses_are_skipped_and_sibling_requirements_survive(self):
        self.assert_statements({'description': '''
            <p>Required Qualifications</p>
            <ul>
                <li>Ability to travel to the locations below:
                    <ul><li>25 Main Street, Austin 78701</li></ul>
                </li>
                <li>Graduate from an accredited Nurse Practitioner or Physician Assistant program.</li>
                <li>Reside within a commutable distance of the clinic.</li>
                <li>Ability to lift up to forty pounds is required.</li>
                <li>Must be able to lift 100 lbs</li>
            </ul>
            <p>Preferred Qualifications</p>
            <ul>
                <li>Ability and willingness to provide coverage at other locations as needed.</li>
                <li>Experience treating pediatric patients.</li>
            </ul>
        '''}, [
            ('ambiguous', 'Ability to travel to the locations below:'),
            ('required', 'Graduate from an accredited Nurse Practitioner or Physician Assistant program.'),
            ('preferred', 'Experience treating pediatric patients.'),
        ])

    def test_choice_lead_in_stays_attached_to_credential_options(self):
        wording = (
            'License/Certification: One of the following is preferred. Licensed Practical Nurse (LPN); '
            'Licensed Social Worker (LSW); Registered Nurse (RN) preferred.'
        )
        self.assert_statements({'description': f'<p>{wording}</p>'}, [('preferred', wording)])

    def test_required_skills_boundary_keeps_occupational_credentials(self):
        self.assert_statements({'description': '''
            <p>Responsibilities:</p>
            <ul><li>Maintain all required certifications and licenses as required by policy.</li></ul>
            <p>Skills and Experience required:</p>
            <ul>
                <li>Current valid CDL Class A or B (must be maintained).</li>
                <li>Valid DOT medical card (must be maintained).</li>
                <li>Comfortable with physical requirements, including repeated lifting up to 70 lbs.</li>
                <li>Flexibility to adjust start/finish times daily.</li>
            </ul>
            <p>Required (Driving Record):</p>
            <ul><li>No more than two violations in the past year.</li></ul>
        '''}, [
            ('required', 'Current valid CDL Class A or B (must be maintained).'),
            ('required', 'Valid DOT medical card (must be maintained).'),
        ])

    def test_explicit_qualifications_recover_after_shift_details(self):
        self.assert_statements({'description': '''
            <p>Shift Details: Monday to Friday from 8:00 a.m. to 4:30 p.m.</p>
            <ul><li>Maintains inventory across sites.</li><li>Must be able to work overtime.</li></ul>
            <ul>
                <li>Bachelor's degree in computer science required, or equivalent experience required.</li>
                <li>Less than 2 years of experience in systems administration required.</li>
                <li>Relevant entry-level certifications (e.g., CompTIA Server+) preferred.</li>
            </ul>
            <p>Compensation: Competitive pay.</p>
            <p>Computer science degree required to qualify for the tuition program.</p>
        '''}, [
            ('ambiguous', 'Must be able to work overtime.'),
            ('required', "Bachelor's degree in computer science required, or equivalent experience required."),
            ('required', 'Less than 2 years of experience in systems administration required.'),
            ('preferred', 'Relevant entry-level certifications (e.g., CompTIA Server+) preferred.'),
        ])

    def test_summary_keeps_required_alternatives_and_separates_explicit_preferences(self):
        self.assert_statements({'description': '''
            <p>Key Details: This is a remote position. Candidates must have an active Compact RN license
            or Florida RN license, with a Compact license preferred. A minimum of 2+ years of acute care
            experience is required, with ER or ICU experience preferred. The schedule is Monday through Friday.</p>
            <p>Education and Work Experience:</p>
            <p>Bachelor's degree required. Advanced degree preferred in behavioral science or a related field.</p>
            <p>Knowledge of quality management systems (preferred), including audit tools.</p>
            <p>License/Certification: Valid state clinical license preferred (i.e.- LPN, RN, etc.)</p>
        '''}, [
            ('required', 'Candidates must have an active Compact RN license or Florida RN license'),
            ('preferred', 'with a Compact license preferred.'),
            ('required', 'A minimum of 2+ years of acute care experience is required'),
            ('preferred', 'with ER or ICU experience preferred.'),
            ('required', "Bachelor's degree required."),
            ('preferred', 'Advanced degree preferred in behavioral science or a related field.'),
            ('preferred', 'Knowledge of quality management systems (preferred), including audit tools.'),
            ('preferred', 'License/Certification: Valid state clinical license preferred (i.e.- LPN, RN, etc.)'),
        ])

    def test_explicit_sections_take_text_bullets_and_reset_at_unmarked_skills(self):
        self.assert_statements({'description': '''
            <p>Minimum Qualifications</p>
            <p>No prior sales experience needed. If you are curious about technology, we want to hear from you.</p>
            <p>· Are organized and able to manage multiple priorities</p>
            <p>Preferred Qualifications</p>
            <ul><li>Experience with account planning.</li></ul>
            <p>Skills &amp; Capabilities:</p>
            <ul><li>Strong analytical skills.</li><li>Ability to travel approximately 70%.</li></ul>
        '''}, [
            ('required', 'Are organized and able to manage multiple priorities'),
            ('preferred', 'Experience with account planning.'),
            ('ambiguous', 'Strong analytical skills.'),
            ('ambiguous', 'Ability to travel approximately 70%.'),
        ])

    def test_mixed_format_boundaries_keep_requirements_without_schedule_or_pay(self):
        self.assert_statements({'description': '''
            <p>Key Details: This position is remote with 75% travel required.
            Candidates must reside in the state of Kansas. Ability to lift up to forty pounds is required.</p>
            <p>This is a fully remote position with a work schedule of 8:00 a.m. to 5:00 p.m.
            Experience with Epic and Excel is preferred.</p>
            <p>Education/Experience: Requires Graduate from an Accredited School of Nursing or Bachelor's degree
            in Nursing and 2 – 4 years of related experience. 2+ years of acute care experience required.</p>
            <p>Experience: Experience in HEDIS or NCQA preferredPay Range: $60,000 annually</p>
            <p>Required Qualifications:</p>
            <ul>
                <li>RN from accredited nursing program. Bachelor's degree in nursing or 4+ years of supervisory experience</li>
                <li>PALS if supervising a pediatric department (within 6 months)</li>
                <li>Willing/able to work at least three holidays per year</li>
                <li>Dedicated remote workspace free from distractions</li>
            </ul>
        '''}, [
            ('ambiguous', 'Key Details: This position is remote with 75% travel required.'),
            ('preferred', 'Experience with Epic and Excel is preferred.'),
            ('required', "Education/Experience: Requires Graduate from an Accredited School of Nursing or Bachelor's "
                         'degree in Nursing and 2 – 4 years of related experience.'),
            ('required', '2+ years of acute care experience required.'),
            ('preferred', 'Experience in HEDIS or NCQA preferred'),
            ('required', 'RN from accredited nursing program.'),
            ('required', "Bachelor's degree in nursing or 4+ years of supervisory experience"),
            ('required', 'PALS if supervising a pediatric department (within 6 months)'),
        ])

    def test_text_bullets_keep_their_shared_experience_minimum(self):
        self.assert_statements({'description': '''
            <p>Minimum Qualifications:</p>
            <p>Requires 5 years of experience in the following skills:</p>
            <p>• Statistical analysis;</p>
            <p>• Querying large datasets using SQL.</p>
            <p>Preferred Qualifications:</p>
            <p>• Strong presentation skills.</p>
        '''}, [
            ('required', 'Requires 5 years of experience in the following skills: '
                         '• Statistical analysis; • Querying large datasets using SQL.'),
            ('preferred', 'Strong presentation skills.'),
        ])

    def test_state_rn_license_is_separate_from_travel_and_schedule(self):
        self.assert_statements({'description': '''
            <p>Key Details: This remote position requires up to 75% local travel for home visits.
            Candidates must hold an active New Jersey Registered Nurse (RN) license.
            Strong preference will be given to candidates who reside in Bergen County.
            The typical schedule is Monday through Friday.</p>
            <p>Required Qualifications:</p>
            <ul><li>Ability/willing to travel approximately 25% of the time</li>
            <li>Able to work the shift hours listed above, plus overtime. (Overtime may be mandatory)</li>
            <li>Travel booking platform experience</li></ul>
        '''}, [
            ('ambiguous', 'Key Details: This remote position requires up to 75% local travel for home visits.'),
            ('required', 'Candidates must hold an active New Jersey Registered Nurse (RN) license.'),
            ('ambiguous', 'Ability/willing to travel approximately 25% of the time'),
            ('ambiguous', 'Able to work the shift hours listed above, plus overtime. (Overtime may be mandatory)'),
            ('required', 'Travel booking platform experience'),
        ])

    def test_neutral_education_reopens_scope_and_distinguishes_explicit_tenure(self):
        self.assert_statements({'description': '''
            <h2>Job Details</h2><p>Lead business operations.</p>
            <p>Education and Experience:</p>
            <p>A graduate degree in a relevant discipline preferred.
            Position requires at least 8+ years of experience in enterprise sales.
            Experience in healthcare sales preferred.</p>
            <p>5+ years of account planning experience.</p>
            <p>Requires broad training in accounting; normally requires a minimum of three years of experience.</p>
            <p>Skills and Knowledge:</p>
            <p>Strong problem-solving skills and the ability to recognize when escalation is required.</p>
        '''}, [
            ('preferred', 'A graduate degree in a relevant discipline preferred.'),
            ('required', 'Position requires at least 8+ years of experience in enterprise sales.'),
            ('preferred', 'Experience in healthcare sales preferred.'),
            ('ambiguous', '5+ years of account planning experience.'),
            ('required', 'Requires broad training in accounting;'),
            ('ambiguous', 'normally requires a minimum of three years of experience.'),
            ('ambiguous', 'Strong problem-solving skills and the ability to recognize when escalation is required.'),
        ])

    def test_line_break_starts_a_labeled_criterion_without_splitting_alternatives(self):
        self.assert_statements({'description': '''
            <p>Required Qualifications:</p><ul>
            <li><span>Demonstrated programming skills in Python or Java</span><br>
            <span>Cloud development: Hands-on experience building and deploying applications.</span></li>
            <li>Current state RN license or<br>Compact RN license before starting work.</li>
            </ul>
        '''}, [
            ('required', 'Demonstrated programming skills in Python or Java'),
            ('required', 'Cloud development: Hands-on experience building and deploying applications.'),
            ('required', 'Current state RN license or Compact RN license before starting work.'),
        ])

    def test_local_travel_and_transportation_are_ambiguous_in_required_sections(self):
        self.assert_statements({'description': '''
            <p>Required Qualifications:</p><ul>
                <li>Ability to travel locally 4 days a week</li>
                <li>Access to reliable transportation and valid driver's license</li>
                <li>Valid driver’s license and reliable transportation</li>
                <li>Current pharmacist license in Maine</li>
                <li>Must have CDL Class A and forklift experience.</li>
            </ul>
        '''}, [
            ('ambiguous', 'Ability to travel locally 4 days a week'),
            ('ambiguous', "Access to reliable transportation and valid driver's license"),
            ('ambiguous', 'Valid driver’s license and reliable transportation'),
            ('required', 'Current pharmacist license in Maine'),
            ('required', 'Must have CDL Class A and forklift experience.'),
        ])

    def test_mobility_and_on_call_scheduling_are_excluded_while_skills_survive(self):
        self.assert_statements({'description': '''
            <p>Required Qualifications:</p>
            <ul>
                <li>Adequate mobility to walk, stand, and lift up to 35 lbs regularly is required.</li>
                <li>Must be available for on-call rotation.</li>
                <li>On-call coverage is required.</li>
                <li>Experience managing on-call scheduling systems.</li>
            </ul>
        '''}, [
            ('required', 'Experience managing on-call scheduling systems.'),
        ])

    def test_ideally_separates_preferred_industry_from_required_experience(self):
        self.assert_statements({'description': '''
            <p>Minimum Qualifications:</p>
            <p>12+ years of experience in pricing strategy or revenue management, ideally within technology or consulting.</p>
            <p>Education/Experience:</p>
            <p>5+ years of experience in billing, preferably in healthcare.</p>
        '''}, [
            ('required', '12+ years of experience in pricing strategy or revenue management'),
            ('preferred', 'ideally within technology or consulting.'),
            ('ambiguous', '5+ years of experience in billing, preferably in healthcare.'),
        ])

    def test_plan_dependent_requirements_and_relocation_do_not_absorb_preferences(self):
        self.assert_statements({'description': '''
            <p>Key Details: Must reside within Oklahoma or be willing to relocate to Oklahoma.
            Foster care experience is preferred.</p>
            <p>Education/Experience: Minimum 1 year of customer service experience preferred.
            Driver's license may be required by some plans.
            Specific language skills may be required by some plans.</p>
            <p>Current state license may be required by certain contracts.</p>
            <p>Current RN license required, and a second license may be required by some plans.</p>
        '''}, [
            ('preferred', 'Foster care experience is preferred.'),
            ('preferred', 'Education/Experience: Minimum 1 year of customer service experience preferred.'),
            ('ambiguous', "Driver's license may be required by some plans."),
            ('ambiguous', 'Specific language skills may be required by some plans.'),
            ('ambiguous', 'Current state license may be required by certain contracts.'),
            ('required', 'Current RN license required, and a second license may be required by some plans.'),
        ])

    def test_key_details_recover_explicit_licenses_experience_and_preferences(self):
        self.assert_statements({'description': '''
            <p>Key Details: Must be licensed in the state of Texas. Pediatric experience required.
            This team supports foster care youth. Previous foster care experience is strongly preferred.
            The regular work schedule is Monday through Friday, with weekend work required.</p>
            <p>License/Certification:</p>
            <ul><li>RN state or compact licensure required or</li>
            <li>Current nurse practitioner license required</li>
            <li>Care management certification must be obtained within 90 days of hire required</li></ul>
        '''}, [
            ('required', 'Must be licensed in the state of Texas.'),
            ('required', 'Pediatric experience required.'),
            ('preferred', 'Previous foster care experience is strongly preferred.'),
            ('required', 'RN state or compact licensure required or Current nurse practitioner license required'),
            ('required', 'Care management certification must be obtained within 90 days of hire required'),
        ])

    def test_preference_in_role_summary_is_separate_from_general_prose(self):
        self.assert_statements({'description': '''
            <p>We are seeking a psychologist who will conduct assessments.
            This remote role combines reviews with strategy work. Familiarity with the local market is important,
            and health plan experience is highly preferred.</p>
        '''}, [
            ('preferred', 'health plan experience is highly preferred.'),
        ])

    def test_independent_preferred_certification_ends_a_desired_choice_list(self):
        self.assert_statements({'description': '''
            <p>Technical Skills:</p>
            <p>One or more of the following skills are desired.</p>
            <ul><li>Experience with application development</li>
            <li>Experience with automated testing</li>
            <li>Salesforce architecture or development certifications preferred, but not required</li></ul>
        '''}, [
            ('preferred', 'One or more of the following skills are desired. Experience with application development '
                          'Experience with automated testing'),
            ('preferred', 'Salesforce architecture or development certifications preferred, but not required'),
        ])

    def test_transportation_and_overtime_are_ambiguous_and_admin_text_is_excluded(self):
        self.assert_statements({'description': '''
            <p>Shift Details: 9 AM to 6 PM</p><p>(Overtime may be required)</p>
            <p>Required Qualifications:</p>
            <ul><li>Current driver's license and vehicle insurance, access to a dependable vehicle, or public transportation</li>
            <li>Proven ability and willingness to travel up to10% of the time</li>
            <li>Available to work a weekend rotation</li><li>Active state pharmacist license</li></ul>
            <p>Preferred Qualifications:</p>
            <ul><li>Current CPR certification or ability to complete within 90 days of hire</li>
            <li>Ability to perform physical tasks required for patient care, including lifting and transferring</li>
            <li>Remote from East Coast region</li></ul>
            <p>All Telecommuters will be required to adhere to the employer's Telecommuter Policy.</p>
            <p>The employer is a drug - free workplace. Candidates are required to pass a drug test.</p>
        '''}, [
            ('ambiguous', '(Overtime may be required)'),
            ('ambiguous', "Current driver's license and vehicle insurance, access to a dependable vehicle, or public transportation"),
            ('ambiguous', 'Proven ability and willingness to travel up to10% of the time'),
            ('required', 'Active state pharmacist license'),
            ('preferred', 'Current CPR certification or ability to complete within 90 days of hire'),
        ])

    def test_adjacent_education_restatement_keeps_the_explicit_equivalent(self):
        self.assert_statements({'description': '''
            <p>Experience and Educational Requirements:</p>
            <p>Requires completion of a high school diploma, general education degree (GED)</p>
            <p>Minimum Skills, Knowledge and Ability Requirements:</p>
            <ul><li>High School Diploma/GED or equivalent experience required.</li>
            <li>Warehouse inventory experience required.</li></ul>
        '''}, [
            ('required', 'High School Diploma/GED or equivalent experience required.'),
            ('required', 'Warehouse inventory experience required.'),
        ])

    def test_cencora_warehouse_keeps_education_equivalence_and_tenure(self):
        self.assert_statements({'description': '''
            Responsibilities:
            Maintain inventory records.
            Experience and Educational Requirements:
            Requires completion of a high school diploma, GED or equivalent combination of experience and education; two (2) plus years of work experience.
            Important Skills
            Knowledge of warehouse operations.
            Must possess basic mathematical skills.
        '''}, [
            ('required', 'Requires completion of a high school diploma, GED or equivalent combination '
                         'of experience and education; two (2) plus years of work experience.'),
            ('ambiguous', 'Knowledge of warehouse operations.'),
            ('required', 'Must possess basic mathematical skills.'),
        ])

    def test_jpmorgan_parallel_headings_and_phillips_qualifier_suffixes(self):
        for required, preferred in (
            ('Required qualifications, capabilities, and skills', 'Preferred qualifications, capabilities and skills'),
            ('What You’ll Bring – Required', 'What Makes You Stand Out – Preferred'),
        ):
            with self.subTest(required=required):
                self.assert_statements({'description': f'''
                    {required}
                    Bachelor’s degree in finance or equivalent experience.
                    {preferred}
                    5+ years of experience in financial analytics.
                '''}, [
                    ('required', 'Bachelor’s degree in finance or equivalent experience.'),
                    ('preferred', '5+ years of experience in financial analytics.'),
                ])

    def test_verizon_extended_preference_heading_and_application_boundary(self):
        self.assert_statements({'description': '''
            You’ll need to have:
            High school diploma or GED.
            Even better if you have one or more of the following:
            Must have experience in commission-based sales.
            Customer service experience is preferred but not required.
            After you apply…
            Experience questionnaire required.
        '''}, [
            ('required', 'High school diploma or GED.'),
            ('preferred', 'Must have experience in commission-based sales.'),
            ('preferred', 'Customer service experience is preferred but not required.'),
        ])

    def test_home_depot_pairs_minimum_table_values_and_skips_placeholders(self):
        self.assert_statements({'description': '''
            <h3>Preferred Qualifications:</h3><ul><li>1–3 years of relevant work experience</li></ul>
            <table>
              <tr><th>Minimum Education</th><td>Trade school degree or equivalent experience.</td></tr>
              <tr><th>Preferred Education</th><td>No additional education</td></tr>
              <tr><th>Minimum Years of Work Experience</th><td>2</td></tr>
              <tr><th>Preferred Years of Work Experience</th><td>No additional years of experience</td></tr>
              <tr><th>Minimum Leadership Experience</th><td>No previous leadership experience</td></tr>
              <tr><th>Certifications</th><td>None</td></tr>
            </table>
            <h3>Competencies</h3><ul><li>Mechanical inclination</li></ul>
        '''}, [
            ('preferred', '1–3 years of relevant work experience'),
            ('required', 'Trade school degree or equivalent experience.'),
            ('required', 'Minimum Years of Work Experience: 2'),
            ('ambiguous', 'Mechanical inclination'),
        ])

    def test_comcast_generic_labels_keep_equivalence_and_ambiguous_range(self):
        self.assert_statements({'description': '''
            Skills:
            Consultative Selling; Relationship Building; Pipeline Management
            Education
            While possessing the stated degree is preferred, applicants may have coursework and experience,
            or extensive related professional experience.
            Relevant Work Experience
            2–5 Years
        '''}, [
            ('ambiguous', 'Consultative Selling; Relationship Building; Pipeline Management'),
            ('preferred', 'While possessing the stated degree is preferred, applicants may have coursework '
                          'and experience, or extensive related professional experience.'),
            ('ambiguous', '2–5 Years'),
        ])

    def test_tenure_in_neutral_sections_requires_explicit_minimum_wording(self):
        result = self.assert_statements({'description': '''
            Qualifications
            BA/BS required, MBA preferred
            8+ years of experience in product marketing or lifecycle management.
            To be successful in this role, you have:
            Experience & Skills
            At least four years of experience developing software.
            5+ years of sales experience, preferably in analytics.
            Experience with data structures.
        '''}, [
            ('required', 'BA/BS required'),
            ('preferred', 'MBA preferred'),
            ('ambiguous', '8+ years of experience in product marketing or lifecycle management.'),
            ('required', 'At least four years of experience developing software.'),
            ('ambiguous', '5+ years of sales experience, preferably in analytics.'),
            ('ambiguous', 'Experience with data structures.'),
        ])
        self.assertEqual(result.evidence[2].confidence, 'medium')

    def test_perplexity_one_of_nested_list_is_one_criterion(self):
        self.assert_statements({'description': '''
            <h3>Qualifications</h3><ul>
              <li>Proven record of meeting or exceeding revenue targets.</li>
              <li>Domain knowledge in at least one of the following areas:
                <ul><li>Harness engineering</li><li>Plugin architectures</li><li>Agent evaluation</li></ul>
              </li>
              <li>Experience with Python.</li>
            </ul><h3>Nice to have</h3><ul><li>5+ years of sales experience.</li></ul>
        '''}, [
            ('ambiguous', 'Proven record of meeting or exceeding revenue targets.'),
            ('ambiguous', 'Domain knowledge in at least one of the following areas: '
                          'Harness engineering Plugin architectures Agent evaluation'),
            ('ambiguous', 'Experience with Python.'),
            ('preferred', '5+ years of sales experience.'),
        ])

    def test_centene_licensure_alternatives_keep_final_option(self):
        self.assert_statements({'description': '''
            <p>License/Certification:</p><ul><li>LCSW license required or</li>
            <li>LMHC license required or</li><li>RN compact state licensure required</li></ul>
            <p>Pay Range: $27 to $50 an hour</p>
        '''}, [
            ('required', 'LCSW license required or LMHC license required or RN compact state licensure required'),
        ])

    def test_meta_flattened_generic_field_does_not_infer_hard_tenure(self):
        text = '10+ years of construction experience Bachelor’s degree or equivalent experience Proficiency in scheduling'
        self.assert_statements({'qualifications': text, 'responsibilities': 'Maintain project records.'}, [
            ('ambiguous', text),
        ])

    def test_nested_heading_scope_ends_with_its_list(self):
        self.assert_statements({'description': '''
            <h3>Required Qualifications</h3><ul>
            <li>Experience with Java.</li>
            <li><ul><li>Preferred Skills:</li><li>5+ years of SQL experience.</li></ul></li>
            <li>Knowledge of network protocols.</li></ul>
            <h3>Our Culture</h3><ul><li>Our staff have experience in training.</li></ul>
        '''}, [
            ('required', 'Experience with Java.'),
            ('preferred', '5+ years of SQL experience.'),
            ('required', 'Knowledge of network protocols.'),
        ])

    def test_boilerplate_and_operational_duties_are_excluded(self):
        self.assert_statements({'description': '''
            Preferred Qualifications:
            Experience with networking hardware.
            Perform equipment repairs documented by licensed specialists.
            Individual pay is determined by education, certifications and experience.
            Must have a degree to enroll in this benefit.
            Required Qualifications:
            Proficiency in configuring switches.
            Benefits:
            A security certification is required to use the benefits website.
        '''}, [
            ('preferred', 'Experience with networking hardware.'),
            ('required', 'Proficiency in configuring switches.'),
        ])

    def test_conditional_registration_is_a_requirement_and_disclosures_are_excluded(self):
        self.assert_statements({'description': '''
            <h3>Preferred Qualifications</h3>
            <p>College degree or military equivalent.</p>
            <h3>Training and Travel Requirement</h3>
            <p>You’ll successfully complete the Branch Manager Training Program.</p>
            <h3>Regulatory eligibility</h3>
            <p>This position is subject to federal qualification requirements for loan originators.
            You must register or update your existing registration upon starting work. Any information
            obtained during registration may be disclosed to regulators.</p>
        '''}, [
            ('preferred', 'College degree or military equivalent.'),
            ('required', 'This position is subject to federal qualification requirements for loan originators. '
                         'You must register or update your existing registration upon starting work.'),
        ])

    def test_conflicting_labels_within_preferred_evidence_never_emit_required(self):
        self.assert_statements({'preferredQualifications': '''
            BA/BS required, MBA preferred
            Required Certifications:
            Active PMP certification.
        '''}, [
            ('ambiguous', 'BA/BS required, MBA preferred'),
            ('ambiguous', 'Active PMP certification.'),
        ])

    def test_explicitly_desired_list_does_not_promote_numerical_values(self):
        self.assert_statements({'description': '''
            <h3>Technical Skills</h3>
            <p>One or more of the following skills are desired.</p>
            <ul><li>5+ years of Kubernetes experience</li><li>5+ years of database experience</li></ul>
        '''}, [
            ('preferred', 'One or more of the following skills are desired. '
                          '5+ years of Kubernetes experience 5+ years of database experience'),
        ])

    def test_run_on_heading_and_pay_do_not_become_part_of_evidence(self):
        self.assert_statements({'description': '''
            Education/Experience: Requires a bachelor's degree or equivalent experience.Pay Range: $40 to $50 per hour
            Minimum QualificationsValid state-issued driver’s license.
            I acknowledge that the position for which I am applying requires an assessment.
            Participate in the quality control program and take appropriate action when required.
        '''}, [
            ('required', "Education/Experience: Requires a bachelor's degree or equivalent experience."),
            ('required', 'Valid state-issued driver’s license.'),
        ])

    def test_work_experience_floor_and_degree_preference_keep_alternatives(self):
        self.assert_statements({'description': '''
            Education
            Bachelor’s degree preferred. Equivalent experience will be considered.
            Work Experience
            Minimum of 7 years in network operations or a related role.
            Language Skills: Preferred fluency in Spanish.
            The company is an equal opportunity employer.
            Our team has experience across many industries.
        '''}, [
            ('preferred', 'Bachelor’s degree preferred. Equivalent experience will be considered.'),
            ('required', 'Minimum of 7 years in network operations or a related role.'),
            ('preferred', 'Language Skills: Preferred fluency in Spanish.'),
        ])
    def test_education_paths_and_independent_skill_minimum_are_separate(self):
        education = ("Master's degree plus one year of relevant experience. "
                     "Employer will accept a bachelor's degree plus five years of experience.")
        skills = ("Must have one year of research or work experience in the following skill(s): "
                  "(1) programming in Java or Python; and (2) evaluating learning models.")
        result = self.assert_statements({'description': f'Basic Qualifications\n{education} {skills}#0000'}, [
            ('required', education),
            ('required', skills),
        ])
        self.assertEqual([item.block for item in result.evidence], [2, 2])

    def test_numbered_skills_keep_every_member_and_the_shared_minimum(self):
        self.assert_statements({'description': '''
            Basic Qualifications
            Must have three years of experience in the following skill(s):
            (1) defining product strategy;
            (2) gathering product requirements;
            (3) using data to improve processes; and
            (4) planning and executing launches.
            Preferred Qualifications
            Experience working with external customers.
        '''}, [
            ('required', 'Must have three years of experience in the following skill(s): '
                         '(1) defining product strategy; (2) gathering product requirements; '
                         '(3) using data to improve processes; and (4) planning and executing launches.'),
            ('preferred', 'Experience working with external customers.'),
        ])

    def test_shared_skill_minimum_applies_only_to_its_attached_html_list(self):
        self.assert_statements({'description': '''
            <h3>Basic Qualifications</h3>
            <p>Must have 2 years of experience in the following skills:</p>
            <ol><li>Forecasting demand</li><li>Maintaining dashboards</li></ol>
            <ul><li>Knowledge of inventory methods.</li></ul>
        '''}, [
            ('required', 'Must have 2 years of experience in the following skills: Forecasting demand Maintaining dashboards'),
            ('required', 'Knowledge of inventory methods.'),
        ])

    def test_explicit_applicant_criteria_survive_summary_and_duty_boundaries(self):
        eligibility = ('Export Control License: This role may require a deemed export control license. '
                       'Placement is contingent on the employer obtaining a license.')
        self.assert_statements({'description': f'''
            You must be comfortable managing remote delivery teams. This role has on-call duties.
            Our technicians work on complex systems. To be successful you need to be detail oriented.
            Responsibilities
            Inspect components and maintain accurate test records.
            Candidates must be 18 years or older and able to follow safety guidelines.
            {eligibility}
        '''}, [
            ('required', 'You must be comfortable managing remote delivery teams.'),
            ('required', 'To be successful you need to be detail oriented.'),
            ('required', 'Candidates must be 18 years or older and able to follow safety guidelines.'),
            ('required', eligibility),
        ])

    def test_basic_fluency_and_specifications_are_kept_apart_from_travel(self):
        self.assert_statements({'description': '''
            Basic Qualifications
            Speak, write, and read fluently in English
            Writes clear and detailed functional specifications.
            Ability to travel to or commute between data center locations as needed
            Willingness to temporarily work at alternative sites during training
            Candidates must be able to travel (over 50 miles) to active data center sites.
            Experience managing a travel booking platform.
            Physical Requirements
            All physical requirements are expected with reasonable accommodations:
            Ability to work in an environment that operates 24/7
        '''}, [
            ('required', 'Speak, write, and read fluently in English'),
            ('required', 'Writes clear and detailed functional specifications.'),
            ('ambiguous', 'Ability to travel to or commute between data center locations as needed'),
            ('ambiguous', 'Candidates must be able to travel (over 50 miles) to active data center sites.'),
            ('required', 'Experience managing a travel booking platform.'),
        ])


    def test_inline_deadline_does_not_hide_explicit_applicant_criteria(self):
        technical = 'Excellent implementation skills with a proven documentation method is also required.'
        collaboration = 'The desire and ability to work in a collaborative environment is essential.'
        self.assert_statements({'description': f'''
            Description
            Application deadline: Applications will be accepted on an ongoing basis
            The ideal candidate should be independent. {technical} {collaboration} The team will install equipment.
            Key responsibilities
            Build production dashboards.
            Basic Qualifications
            Have an available online portfolio
        '''}, [
            ('required', technical),
            ('required', collaboration),
            ('required', 'Have an available online portfolio'),
        ])

    def test_explicit_skills_are_retained_in_mixed_role_prose(self):
        construction = ('This role requires strong construction expertise, commercial acumen, '
                        'and the ability to manage concurrent projects independently.')
        analytical = 'In addition, you must possess strong analytical skills with demonstrated problem solving ability.'
        self.assert_statements({'description': f'''
            Description
            {construction} You will manage budgets and coordinate the work.
            Key responsibilities
            To be successful you should be curious. {analytical} You will support the team.
        '''}, [
            ('required', construction),
            ('required', analytical),
        ])

    def test_duty_lead_and_mixed_travel_do_not_hide_a_license_requirement(self):
        license_requirement = ("You will be responsible for having a reliable personal vehicle and a valid driver's license "
                               "to travel within the regional work area.")
        self.assert_statements({'description': f'''
            Work prioritization and communication are critical to success. Traveling within the regional work area is required.
            Essential Requirements
            As a technician, you have good technical abilities and demonstrate a breadth of knowledge while you:
            -Take ownership of technical issues.
            -Solve problems at their root.
            -Maintain service level agreements.
            You will be required to work shift work. Traveling within the regional work area is required. {license_requirement}
            Basic Qualifications
            High school diploma or equivalent
        '''}, [
            ('ambiguous', 'Traveling within the regional work area is required.'),
            ('required', license_requirement),
            ('required', 'High school diploma or equivalent'),
        ])

    def test_travel_sentence_stays_separate_from_shared_skills_requirement(self):
        education = "Master's degree and one year of experience or bachelor's degree and five years of experience."
        skills = ('Must have one year of experience in the following skill(s): '
                  '(1) administering Linux or Windows; and (2) automating network operations.')
        travel = 'Domestic and/or international travel up to 25% to perform role responsibilities may be required.'
        self.assert_statements({'description': f'Basic Qualifications\n{education} {skills} {travel}#0000'}, [
            ('required', education),
            ('required', skills),
            ('ambiguous', travel),
        ])

    def test_logistics_and_physical_demands_do_not_become_resume_qualifications(self):
        self.assert_statements({'description': '''
            Travel up to 50% may be required
            Basic Qualifications
            Can carry/lift up to 50 lbs, stand/walk during shifts, and frequently bend and reach
            Can lift up to 49 pounds during shifts
            Ability to train as a drone operator and adhere to standards.
            Willingness to participate in shift rotations to support 24/7 data center operations
            Experience designing shift scheduling systems.
            Physical Requirements
            Willingness and demonstrated ability to work in the following physical conditions with reasonable accommodations:
        '''}, [
            ('ambiguous', 'Travel up to 50% may be required'),
            ('required', 'Experience designing shift scheduling systems.'),
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
