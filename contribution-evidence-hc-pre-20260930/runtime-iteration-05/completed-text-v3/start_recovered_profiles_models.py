from pathlib import Path
import subprocess
root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
assert not (root / 'controller-v10.pid').exists()
assert not (root / 'controller-v10.exit').exists()
assert (root / 'controller-v9.exit').read_text().strip() == '0'
assert 'SHORT_DIV_RECOVERED_ORDER_CONTROLS_COMPLETE' in (root / 'controller-v9.log').read_text()
subprocess.run(['python', str(root / 'foreign_jobs.py')], check=True)
prior_pid = int((root / 'controller-v9.pid').read_text())
assert not (Path('/proc') / str(prior_pid)).exists()
with (root / 'controller-v10.log').open('xb') as log:
    p = subprocess.Popen(['bash', str(root / 'controller_v10.sh')], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', p.pid)
