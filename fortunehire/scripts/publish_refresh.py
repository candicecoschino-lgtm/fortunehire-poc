"""Publish validated data without overwriting concurrent site or data updates."""
from pathlib import Path
import subprocess

DATA_PATHS=('public/data/jobs.json','public/data/collection-status.json','automation/state.json',
            'public/data/resume-qualifications.json')

def publish(root,runner=subprocess.run):
 def git(*args,check=True):
  result=runner(['git',*args],cwd=root,text=True,capture_output=True)
  if check and result.returncode:raise RuntimeError('git '+args[0]+' failed: '+result.stderr[-1200:])
  return result
 git('config','user.name','fortunehire-updates')
 git('config','user.email','fortunehire-updates@users.noreply.github.com')
 base=git('rev-parse','HEAD').stdout.strip();local_base=base
 git('add','--',*DATA_PATHS)
 difference=git('diff','--cached','--quiet',check=False)
 if difference.returncode==0:return 'unchanged'
 if difference.returncode!=1:raise RuntimeError('Could not inspect staged publication data')
 git('commit','-m','Refresh official FortuneHire pilot postings')
 for attempt in range(3):
  git('fetch','origin','main')
  remote=git('rev-parse','origin/main').stdout.strip()
  changed=git('diff','--quiet',base,remote,'--',*DATA_PATHS,check=False)
  if changed.returncode==1:
   print('Newer publication data is already on main; retaining it instead of overwriting it with this older run.')
   return 'superseded'
  if changed.returncode!=0:raise RuntimeError('Could not compare incoming publication data')
  if remote!=local_base:
   rebased=git('rebase','--onto',remote,local_base,check=False)
   if rebased.returncode:
    git('rebase','--abort',check=False)
    raise RuntimeError('Publication could not be rebased safely; remote data was not overwritten.')
   local_base=remote
  pushed=git('push','origin','HEAD:main',check=False)
  if pushed.returncode==0:return 'published'
  if 'fetch first' not in pushed.stderr and 'non-fast-forward' not in pushed.stderr:
   raise RuntimeError('Publication push failed: '+pushed.stderr[-1200:])
  print('Main advanced during publication; checking for a safe retry ('+str(attempt+1)+'/3).')
 raise RuntimeError('Main advanced repeatedly; publication stopped without forcing an update.')

if __name__=='__main__':
 print('Refresh publication: '+publish(Path(__file__).resolve().parents[1]))
