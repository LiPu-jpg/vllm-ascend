"""Start once, only after prior profiling/model stage is terminal and guards pass."""
from pathlib import Path
import subprocess
import hashlib
import json
root = Path('/mnt/workspace/hc-pre-reduction-20260930')
iteration = root / 'iteration-07'
assert not (iteration / 'controller-v1.pid').exists()
assert not (iteration / 'controller-v1.exit').exists()
assert (root / 'iteration-05/controller-v10.exit').exists(), 'Complete prior profiles/models first'
for record in root.glob('iteration-*/controller*.pid'):
    pid = int(record.read_text().strip())
    try:
        words = (Path('/proc') / str(pid) / 'cmdline').read_bytes()
    except FileNotFoundError:
        continue
    assert str(root).encode() not in words, f'Own controller still live: {record}'
frozen = json.loads((iteration / 'frozen-input-sha256.json').read_text())
for relative, expected in frozen.items():
    assert hashlib.sha256((iteration / relative).read_bytes()).hexdigest() == expected, relative
subprocess.run(['python', str(iteration / 'foreign_jobs.py')], check=True)
with (iteration / 'controller-v1.log').open('xb') as log:
    child = subprocess.Popen(['bash', str(iteration / 'controller_v1.sh')], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', child.pid)
