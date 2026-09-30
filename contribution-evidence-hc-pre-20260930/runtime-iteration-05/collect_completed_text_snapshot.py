"""Collect a new immutable snapshot of completed text evidence, without reruns."""
from pathlib import Path
import io
import subprocess
import tarfile
root = Path(__file__).resolve().parent
output = root / "completed-text-v3"
assert not output.exists()
script = r"""
from pathlib import Path
import sys, tarfile
root=Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
labels=[]
for folder in root.iterdir():
 if folder.is_dir() and folder.name.startswith(('div1-','div2-','div4-')) and (folder/'run.exit').exists(): labels.append(folder)
files=[p for p in root.iterdir() if p.is_file() and p.suffix in ('.json','.txt','.log','.pid','.exit','.patch','.sh','.py','.md')]
for folder in labels + [root/'full-extension-build-baseline',root/'full-extension-build-candidate']:
 for p in folder.rglob('*'):
  if p.is_file() and not any('cache' in part for part in p.relative_to(root).parts) and p.suffix in ('.json','.txt','.log','.xml','.csv','.tsv','.patch','.py','.md'):
   files.append(p)
  elif p.is_file() and p.name=='run.exit': files.append(p)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as tar:
 for p in sorted(set(files)): tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','devenvc','python -'],input=script.encode(),stdout=subprocess.PIPE,check=True)
output.mkdir()
with tarfile.open(fileobj=io.BytesIO(r.stdout),mode='r:') as tar:
 tar.extractall(output,filter='data')
print('SNAPSHOT_FILES',sum(p.is_file() for p in output.rglob('*')))
