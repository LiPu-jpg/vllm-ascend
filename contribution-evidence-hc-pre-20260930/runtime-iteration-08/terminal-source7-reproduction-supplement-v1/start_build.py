"""Start matched private builds once, after checking actual prior controllers."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path('/mnt/workspace/hc-pre-reduction-20260930')
iteration = root / 'iteration-08'
assert (root / 'iteration-07/controller-hf32-rounding.exit').read_text().strip() == '0'
for suffix in ('pid', 'exit', 'log'):
    assert not (iteration / f'controller-v1.{suffix}').exists(), suffix
for record in root.glob('iteration-*/controller*.pid'):
    try:
        words = (Path('/proc') / record.read_text().strip() / 'cmdline').read_bytes()
    except FileNotFoundError:
        continue
    assert str(root).encode() not in words, f'Own controller still live: {record}'
for relative, expected in json.loads((iteration / 'frozen-input-sha256.json').read_text()).items():
    assert hashlib.sha256((iteration / relative).read_bytes()).hexdigest() == expected, relative
subprocess.run(['python3', str(iteration / 'foreign_jobs.py')], check=True)
with (iteration / 'controller-v1.log').open('xb') as log:
    child = subprocess.Popen(['bash', str(iteration / 'controller_v1.sh')],
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', child.pid)
