"""One-shot CPU-only analysis; retain all raw NPU outcomes unchanged."""
from pathlib import Path
import subprocess

iteration = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-07')
assert (iteration / 'controller-hf32-rounding.exit').read_text().strip() == '0'
for suffix in ('pid', 'exit', 'log'):
    assert not (iteration / f'controller-saved-cpu-v1.{suffix}').exists()
assert not (iteration / 'saved-benchmark-cpu-hf32-v1').exists()
subprocess.run(['python3', str(iteration / 'foreign_jobs.py')], check=True)
with (iteration / 'controller-saved-cpu-v1.log').open('xb') as log:
    child = subprocess.Popen(['bash', str(iteration / 'controller_saved_cpu_v1.sh')],
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', child.pid)
