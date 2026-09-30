from pathlib import Path
import subprocess
root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
assert not (root / 'controller-v5.pid').exists()
assert not (root / 'controller-v5.exit').exists()
subprocess.run(['python', str(root / 'foreign_jobs.py')], check=True)
assert not Path('/proc/1408363').exists(), 'Inspect the original controller before continuing'
with (root / 'controller-v5.log').open('xb') as log:
    p = subprocess.Popen(['bash', str(root / 'controller_v5.sh')], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', p.pid)
