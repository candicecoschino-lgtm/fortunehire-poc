import sys,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from source_limits import policy
class SourceLimitTests(unittest.TestCase):
 def test_invalid_budgets_cannot_remove_pacing_or_expand_the_pilot(self):
  for key,value in [('maxTracked',101),('maxNew',21),('requestDelaySeconds',0),('maxNew',True),('maxTracked',2.5)]:
   with self.assertRaises(ValueError):policy({'sources':{'microsoft':{key:value}}},'microsoft')
 def test_run_honors_smaller_source_budget_and_code_push_never_adds_jobs(self):
  for requested,expected in [(0,0),(20,2)]:
   with self.subTest(requested=requested),tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);c.atomic_json(root/'public/data/jobs.json',{'schemaVersion':1,'jobs':[]})
    client=Mock(discovery_dates={},discovery_limited=False,discovery_warnings=[])
    report={'errors':[],'checked':0,'added':0,'activeTracked':0}
    with patch.dict(c.SOURCES,{'microsoft':('apply.careers.microsoft.com','Technology')},clear=True),patch.dict(c.REGISTRY,{'sources':{'microsoft':{'maxTracked':10,'maxNew':2,'requestDelaySeconds':6}}},clear=True),patch.object(c,'Client',return_value=client) as ctor,patch.object(c,'discover',return_value={}),patch.object(c,'reconcile',return_value=([],{},report)) as reconcile:
     self.assertTrue(c.run(root,max_new=requested));ctor.assert_called_once_with('apply.careers.microsoft.com',delay=6);self.assertEqual(reconcile.call_args.kwargs['max_new'],expected);self.assertEqual(reconcile.call_args.kwargs['cap'],10)
