import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from employment_type import resolve_employment,apply_employment_policy
import collect_jobs as c
from test_collector import body,URL,NOW

class EmploymentTypeTests(unittest.TestCase):
 def test_unspecified_remains_unspecified_and_preserves_employer_evidence(self):
  old={'title':'Analyst','employmentType':'Not specified','evidence':{'arrangement':''},'postedAt':'2026-11-12','reviewedAt':'2026-11-13','sourceHash':'original'}
  new=apply_employment_policy(old)
  self.assertEqual(new['employmentType'],'Not specified');self.assertNotIn('employmentTypeBasis',new)
  self.assertEqual(new['evidence'],old['evidence'])
  for key in ['postedAt','reviewedAt','sourceHash']:self.assertEqual(new[key],old[key])
  self.assertEqual(apply_employment_policy(new),new)
 def test_verified_types_are_preserved_and_later_title_evidence_replaces_the_assumption(self):
  for kind in ['Full-time','Part-time','Contract','Temporary','Internship']:
   old={'title':'Analyst','employmentType':kind,'evidence':{}}
   self.assertEqual(apply_employment_policy(old),old)
  old={'title':'Analyst','employmentType':'Full-time','employmentTypeBasis':'assumed-full-time','employmentTypeNote':'Assumed full-time.','evidence':{}}
  self.assertEqual(apply_employment_policy(old)['employmentType'],'Not specified')
  new=apply_employment_policy({**old,'title':'Analyst (Part-Time)'})
  self.assertEqual(new['employmentType'],'Part-time');self.assertNotIn('employmentTypeBasis',new);self.assertNotIn('employmentTypeNote',new)
 def test_verizon_time_type_must_match_the_same_role_id_and_title(self):
  url='https://mycareer.verizon.com/jobs/r-test'
  primary={'Id':'r-test','Reference':'R-TEST','Title':'Synthetic specialist','DisplayDate':'2026-11-12','DueDate':None,'Urls':[{'Url':url}],'Locations':[{'City':'Austin','Region':'Texas','Country':'US'}]}
  def page(schedule):
   def stream(value,index):return '<script>self.__next_f.push('+json.dumps([1,str(index)+':'+json.dumps(value)+'\n'])+')</script>'
   return stream(primary,1)+stream({'job':schedule},2)+'<main data-testid="job-page" data-job-id="r-test"><div class="wysiwyg">Benefits for part-time workers differ.</div></main>'
  from unittest.mock import patch
  with patch.dict(c.SOURCES,{'verizon':('mycareer.verizon.com','Telecommunications')}):
   valid={'Id':'r-test','Title':primary['Title'],'TimeType':'Full time'}
   job=c.normalize_posting(page(valid),url,'verizon',NOW)
   self.assertEqual(job['employmentType'],'Full-time');self.assertIn('Verizon TimeType',job['evidence']['employmentType'])
   for invalid in [{**valid,'Id':'r-other'},{**valid,'Title':'Different role'}]:
    self.assertEqual(c.normalize_posting(page(invalid),url,'verizon',NOW)['employmentType'],'Not specified')
 def test_explicit_title_terms_fill_missing_types_without_substring_false_matches(self):
  for title,expected in [('Mold Maker - Full Time','Full-time'),('Warehouse Worker - Fulltime Shifts','Full-time'),('Operations Intern - Summer 2027','Internship'),('Sales Associate (Seasonal)','Temporary'),('Temporary Associate','Temporary'),('Recruiting Coordinator [Contract]','Contract')]:
   kind,evidence=resolve_employment(title,'');self.assertEqual(kind,expected);self.assertIn('title',evidence)
  for title in ['Contracts Manager','Contractor Management Coordinator','Internal Auditor','International Affairs','PT Physical Therapist']:
   self.assertEqual(resolve_employment(title,'')[0],'Not specified')
 def test_structured_and_role_scoped_schedule_labels_are_read(self):
  for description in ['Time Type: Full time','Employment Type: Full_time','Job Schedule: Fulltime','This is a regular full-time position.','This role will be a full-time role.']:
   self.assertEqual(resolve_employment('Analyst',description)[0],'Full-time',description)
  self.assertEqual(resolve_employment('Analyst','',raw_type='PART_TIME')[0],'Part-time')
 def test_generic_labels_hours_benefits_and_work_arrangement_frequency_do_not_supply_schedule(self):
  for description in ['Benefits apply to full-time and part-time employees.','Salary is based on full-time employment.','This role enables associates to work virtually full-time.','Work hours: 40 hours per week.','Employment Type: Regular','Employment Type: Casual','This position is full-time or part-time.']:
   self.assertEqual(resolve_employment('Analyst',description)[0],'Not specified',description)
  for raw in ['Regular','Casual','OTHER','INTERNAL','FULL_TIME PART_TIME']:
   self.assertEqual(resolve_employment('Analyst','',raw_type=raw)[0],'Not specified')
 def test_title_backfill_preserves_source_dates_locations_and_existing_declared_types(self):
  old={'title':'Summer Intern','employmentType':'Not specified','postedAt':'2026-11-12','reviewedAt':'2026-11-13','sourceHash':'original','locations':[{'city':'Austin','state':'Texas'}],'evidence':{}}
  new=apply_employment_policy(old);self.assertEqual(new['employmentType'],'Internship')
  for key in ['postedAt','reviewedAt','sourceHash','locations']:self.assertEqual(new[key],old[key])
  self.assertEqual(old['employmentType'],'Not specified')
  self.assertEqual(apply_employment_policy({**old,'employmentType':'Contract'})['employmentType'],'Contract')
 def test_navigation_and_similar_jobs_cannot_supply_employment_type(self):
  page=body(title='Analyst',description='Role duties.')+'<nav>Time Type: Full-time. Internship programs.</nav>'
  self.assertEqual(c.normalize_posting(page,URL,'boeing',NOW)['employmentType'],'Not specified')
