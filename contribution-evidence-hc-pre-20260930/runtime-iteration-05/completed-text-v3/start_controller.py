"""Start exactly once; observation failures must inspect this same process."""
import argparse
from pathlib import Path
import subprocess

root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
parser = argparse.ArgumentParser()
parser.add_argument('--stage', type=int, choices=(2, 3, 4), required=True)
args = parser.parse_args()
stage = args.stage
assert not (root / f'controller-v{stage}.pid').exists()
assert not (root / f'controller-v{stage}.exit').exists()
if stage > 2:
    predecessor = stage - 1
    marker = ('SHORT_DIV_INITIAL_VALIDATION_COMPLETE' if stage == 3
              else 'SHORT_DIV_ORDER_CONTROLS_COMPLETE')
    assert (root / f'controller-v{predecessor}.exit').read_text().strip() == '0'
    assert marker in (root / f'controller-v{predecessor}.log').read_text()
# Run the authoritative foreign guard BEFORE starting a controller of our own.
subprocess.run(['python', str(root / 'foreign_jobs.py')], check=True)
with (root / f'controller-v{stage}.log').open('xb') as log:
    process = subprocess.Popen(
        ['bash', str(root / f'controller_v{stage}.sh')],
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
print('STARTED_PID', process.pid)
