"""Copy immutable completed reports and guard records; never rerun device work."""
import json
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parent
remote='/mnt/workspace/hc-pre-reduction-20260930/iteration-05'
labels=[f'div4-graph-aa-{x}' for x in ('a1','b1','b2','a2')]
labels += [f'div4-graph-{x}' for x in ('candidate-a','baseline-a','baseline-b','candidate-b')]
labels += [f'div4-event-{x}' for x in ('baseline-a','candidate-a','candidate-b','baseline-b')]
labels += [f'div4-event-aa-{x}' for x in ('a1','b1','b2','a2')]
for label in labels:
    folder=root/'completed'/label
    (folder/'data').mkdir(parents=True,exist_ok=True)
    mode='event' if '-event-' in label else 'graph'
    names=['data/results.json','run.exit','npu-before.txt','npu-after.txt','foreign-before.json','foreign-after.json','other-jobs.txt','other-jobs-after.txt','source-head.txt','source-status.txt',f'{mode}-module-paths.json',f'{mode}-libraries.txt']
    for name in names:
        path=folder/name
        if not path.exists():
            subprocess.run(['scp','-q','-O',f'devenvc:{remote}/{label}/{name}',str(path)],check=True)
    report=json.loads((folder/'data/results.json').read_text())
    assert len(report['cases'])==28 and report['timing']==mode
    assert (folder/'run.exit').read_text().strip()=='0'
    assert json.loads((folder/'foreign-before.json').read_text())==[]
    assert json.loads((folder/'foreign-after.json').read_text())==[]
    assert 'No running processes' in (folder/'npu-before.txt').read_text()
    assert 'No running processes' in (folder/'npu-after.txt').read_text()
    print('COPIED_AND_GUARDS_PASS',label,flush=True)
