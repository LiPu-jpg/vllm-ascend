from pathlib import Path
import subprocess
root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
assert not (root / 'controller-v8.pid').exists()
assert not (root / 'controller-v8.exit').exists()
assert (root / 'controller-v7.exit').read_text().strip() == '0'
assert 'SHORT_DIV_ORDER_CONTROLS_WITH_RETAINED_FAILURES_COMPLETE' in (root / 'controller-v7.log').read_text()
subprocess.run(['python', str(root / 'foreign_jobs.py')], check=True)
assert not Path('/proc/1421700').exists()
with (root / 'controller-v8.log').open('xb') as log:
    p = subprocess.Popen(['bash', str(root / 'controller_v8.sh')], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', p.pid)
