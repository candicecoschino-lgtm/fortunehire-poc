"""An explicit part-time title supplies employment type, not generic benefits or PT."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from test_collector import body,URL,NOW

class TitleEmploymentTests(unittest.TestCase):
 def test_part_time_title_variants_are_part_time(self):
  for title in ['Retail Associate (part-time)','PART TIME Pharmacist','Material Handler - Part Time (Warehouse like)','Part\u2011Time Sales Associate','Part\u2013time Clerk','Part-Time-Time Attendant']:
   job=c.normalize_posting(body(title=title,description='Role duties.'),URL,'boeing',NOW)
   self.assertEqual(job['employmentType'],'Part-time',title)
   self.assertIn('Employer job title explicitly states',job['evidence']['employmentType'])
 def test_explicit_part_time_title_wins_over_a_generic_full_time_metadata_value(self):
  job=c.normalize_posting(body(title='Store Associate (Part-Time)',employmentType='FULL_TIME'),URL,'boeing',NOW)
  self.assertEqual(job['employmentType'],'Part-time')
 def test_unrelated_title_words_and_benefits_do_not_set_job_type(self):
  for title in ['PT Physical Therapist','Department Timekeeper','Partial Time Series Analyst']:
   job=c.normalize_posting(body(title=title,description='Benefits are available to part-time and full-time employees.'),URL,'boeing',NOW)
   self.assertEqual(job['employmentType'],'Not specified')
 def test_other_declared_job_types_remain_intact_without_a_part_time_title(self):
  for declared,expected in [('FULL_TIME','Full-time'),('CONTRACT','Contract'),('TEMPORARY','Temporary'),('INTERN','Internship')]:
   job=c.normalize_posting(body(title='Synthetic specialist',employmentType=declared),URL,'boeing',NOW)
   self.assertEqual(job['employmentType'],expected)
 def test_repeated_refresh_preserves_the_title_based_type(self):
  fetch=lambda url:(200,body(title='Retail Associate (Part-Time)'))
  jobs,state,report=c.reconcile('boeing',[],{}, {'12345':URL},fetch,NOW,max_new=1)
  again,state,report=c.reconcile('boeing',jobs,state,{},fetch,NOW,max_new=0)
  self.assertEqual(again[0]['employmentType'],'Part-time');self.assertEqual(report['added'],0);self.assertEqual(report['changed'],0)
