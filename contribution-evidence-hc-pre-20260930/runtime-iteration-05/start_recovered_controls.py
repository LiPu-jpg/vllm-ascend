from pathlib import Path
import subprocess
root=Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
assert not (root/'controller-v9.pid').exists()
assert not (root/'controller-v9.exit').exists()
assert (root/'controller-v7.exit').read_text().strip()=='1'
assert not Path('/proc/1421700').exists()
subprocess.run(['python',str(root/'foreign_jobs.py')],check=True)
with (root/'controller-v9.log').open('xb') as log:
    p=subprocess.Popen(['bash',str(root/'controller_v9.sh')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print('STARTED_PID',p.pid)
