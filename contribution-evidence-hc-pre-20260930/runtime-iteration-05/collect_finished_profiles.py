"""Copy only terminal diagnostic arms; never restart or read incomplete exports."""
from pathlib import Path
import io, subprocess, tarfile
root=Path(__file__).resolve().parent
output=root/'completed-profile-text-v1'
assert not output.exists()
script=r"""
from pathlib import Path
import sys,tarfile
root=Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
labels=[f'div3-profile-{mode}-{variant}' for mode in ('eager','graph') for variant in ('baseline','candidate')]
for label in labels: assert (root/label/'run.exit').read_text().strip()=='0',label
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as tar:
 for label in labels:
  for p in sorted((root/label).rglob('*')):
   if p.is_file() and (p.suffix in ('.csv','.json','.txt','.log','.tsv') or p.name=='run.exit'):
    tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','devenvc','python -'],input=script.encode(),stdout=subprocess.PIPE,check=True)
output.mkdir()
with tarfile.open(fileobj=io.BytesIO(r.stdout),mode='r:') as tar: tar.extractall(output,filter='data')
print('COPIED_FINISHED_PROFILE_TEXT',sum(p.is_file() for p in output.rglob('*')))
