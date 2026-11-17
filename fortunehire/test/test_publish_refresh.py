import sys,subprocess,tempfile,unittest,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from publish_refresh import publish,DATA_PATHS

@unittest.skipUnless(shutil.which('git'),'Git is required for publication integration checks')
class PublishRefreshTests(unittest.TestCase):
 def git(self,root,*args):
  result=subprocess.run(['git',*args],cwd=root,text=True,capture_output=True)
  if result.returncode:raise RuntimeError(result.stderr)
  return result.stdout.strip()
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='fortunehire-publish-');self.root=Path(self.temp.name).resolve()
  assert self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()) and self.root.name.startswith('fortunehire-publish-')
  self.remote=self.root/'remote.git';self.editor=self.root/'editor';self.worker=self.root/'worker'
  self.git(self.root,'init','--bare',str(self.remote));self.editor.mkdir();self.git(self.editor,'init','-b','main')
  self.git(self.editor,'config','user.name','Test');self.git(self.editor,'config','user.email','test@example.invalid')
  for name in DATA_PATHS:
   target=self.editor/'fortunehire'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('initial',encoding='utf-8')
  (self.editor/'fortunehire/public/index.html').write_text('original site',encoding='utf-8')
  self.git(self.editor,'add','.');self.git(self.editor,'commit','-m','Initial');self.git(self.editor,'remote','add','origin',str(self.remote));self.git(self.editor,'push','-u','origin','main')
  self.git(self.remote,'symbolic-ref','HEAD','refs/heads/main');self.git(self.root,'clone','--depth','1','--no-local',str(self.remote),str(self.worker))
  self.assertEqual(self.git(self.worker,'rev-parse','--is-shallow-repository'),'true')
  (self.worker/'fortunehire/public/data/jobs.json').write_text('worker refresh',encoding='utf-8')
 def tearDown(self):
  # Verify the exact recursive-cleanup target is our owned temporary workspace.
  assert self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()) and self.root.name.startswith('fortunehire-publish-')
  self.temp.cleanup()
 def upstream(self,path,value):
  (self.editor/'fortunehire'/path).write_text(value,encoding='utf-8');self.git(self.editor,'add','.');self.git(self.editor,'commit','-m','Concurrent update');self.git(self.editor,'push')
 def remote_file(self,path):return self.git(self.remote,'show','main:fortunehire/'+path)
 def test_site_update_during_collection_is_preserved_with_the_new_data(self):
  self.upstream('public/index.html','new city search')
  self.assertEqual(publish(self.worker/'fortunehire'),'published')
  self.assertEqual(self.remote_file('public/index.html'),'new city search');self.assertEqual(self.remote_file('public/data/jobs.json'),'worker refresh')
 def test_newer_data_is_never_replaced_by_a_stale_run(self):
  self.upstream('public/data/jobs.json','newer user-approved data')
  before=self.git(self.remote,'rev-parse','main')
  self.assertEqual(publish(self.worker/'fortunehire'),'superseded')
  self.assertEqual(self.git(self.remote,'rev-parse','main'),before);self.assertEqual(self.remote_file('public/data/jobs.json'),'newer user-approved data')
 def test_push_race_is_retried_without_forcing_or_losing_site_changes(self):
  raced=False
  def runner(command,**kwargs):
   nonlocal raced
   if command[:2]==['git','push'] and not raced:raced=True;self.upstream('public/index.html','site changed just before push')
   return subprocess.run(command,**kwargs)
  self.assertEqual(publish(self.worker/'fortunehire',runner=runner),'published')
  self.assertEqual(self.remote_file('public/index.html'),'site changed just before push');self.assertEqual(self.remote_file('public/data/jobs.json'),'worker refresh')
