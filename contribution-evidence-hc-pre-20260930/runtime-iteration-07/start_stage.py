"""Launch a never-started stage after actual predecessor completion and idle guards."""
import argparse
from pathlib import Path
import subprocess
import hashlib
import json
parser = argparse.ArgumentParser()
parser.add_argument('stage', type=int, choices=(2, 3))
args = parser.parse_args()
root = Path('/mnt/workspace/hc-pre-reduction-20260930')
iteration = root / 'iteration-07'
assert not (iteration / f'controller-v{args.stage}.pid').exists()
assert not (iteration / f'controller-v{args.stage}.exit').exists()
previous = args.stage - 1
assert (iteration / f'controller-v{previous}.exit').read_text().strip() == '0'
marker = 'PREFETCH_X_MATCHED_BUILDS_COMPLETE' if args.stage == 2 else 'PREFETCH_X_CORRECTNESS_RESULTS_RECORDED_WITH_FAILURES'
assert marker in (iteration / f'controller-v{previous}.log').read_text()
for record in root.glob('iteration-*/controller*.pid'):
    try:
        words = (Path('/proc') / record.read_text().strip() / 'cmdline').read_bytes()
    except FileNotFoundError:
        continue
    assert str(root).encode() not in words, f'Own controller live: {record}'
frozen = json.loads((iteration / 'frozen-input-sha256.json').read_text())
for relative, expected in frozen.items():
    assert hashlib.sha256((iteration / relative).read_bytes()).hexdigest() == expected, relative
subprocess.run(['python', str(iteration / 'foreign_jobs.py')], check=True)
with (iteration / f'controller-v{args.stage}.log').open('xb') as log:
    child = subprocess.Popen(['bash', str(iteration / f'controller_v{args.stage}.sh')], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', child.pid)
