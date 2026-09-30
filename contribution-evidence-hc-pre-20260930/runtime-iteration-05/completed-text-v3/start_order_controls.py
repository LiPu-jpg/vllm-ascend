from pathlib import Path
import subprocess
root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
assert not (root / 'controller-v7.pid').exists()
assert not (root / 'controller-v7.exit').exists()
subprocess.run(['python', str(root / 'foreign_jobs.py')], check=True)
assert not Path('/proc/1421212').exists()
with (root / 'controller-v7.log').open('xb') as log:
    p = subprocess.Popen(['bash', str(root / 'controller_v7.sh')], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', p.pid)
