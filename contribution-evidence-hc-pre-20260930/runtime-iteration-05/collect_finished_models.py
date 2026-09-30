"""Retain terminal model arms including the failed foreign-after guard."""
from pathlib import Path
import io,subprocess,tarfile
root=Path(__file__).resolve().parent
output=root/'completed-model-text-v1'
assert not output.exists()
script=r"""
from pathlib import Path
import sys,tarfile
root=Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
labels=[f'div3-model-{mode}-{variant}' for mode in ('eager','graph') for variant in ('baseline','candidate')]
for label in labels: assert (root/label/'run.exit').exists(),label
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as tar:
 for label in labels:
  for p in sorted((root/label).rglob('*')):
   if p.is_file() and (p.suffix in ('.csv','.json','.txt','.log','.tsv') or p.name=='run.exit'):
    tar.add(p,arcname=str(p.relative_to(root)),recursive=False)
 for name in ('controller-v10.log','controller-v10.pid','controller-v10.exit','source-before-model-baseline.patch','source-before-model-candidate.patch','source-model-prerequisite-baseline.patch','source-model-prerequisite-candidate.patch'):
  p=root/name; assert p.exists(); tar.add(p,arcname=name,recursive=False)
"""
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','devenvc','python -'],input=script.encode(),stdout=subprocess.PIPE,check=True)
output.mkdir()
with tarfile.open(fileobj=io.BytesIO(r.stdout),mode='r:') as tar:tar.extractall(output,filter='data')
print('COPIED_TERMINAL_MODEL_TEXT',sum(p.is_file() for p in output.rglob('*')))
