"""One-shot guarded diagnostic; never restart an existing controller."""
import hashlib
import json
from pathlib import Path
import subprocess
root = Path('/mnt/workspace/hc-pre-reduction-20260930')
iteration = root / 'iteration-07'
for suffix in ('pid', 'exit', 'log'):
    assert not (iteration / f'controller-hf32-rounding.{suffix}').exists(), suffix
assert (iteration / 'controller-hf32-bit.exit').read_text().strip() == '0'
for record in root.glob('iteration-*/controller*.pid'):
    try:
        words = (Path('/proc') / record.read_text().strip() / 'cmdline').read_bytes()
    except FileNotFoundError:
        continue
    assert str(root).encode() not in words, f'Own controller live: {record}'
for manifest in ('frozen-input-sha256.json', 'hf32-rounding-input-sha256.json'):
    for relative, expected in json.loads((iteration / manifest).read_text()).items():
        assert hashlib.sha256((iteration / relative).read_bytes()).hexdigest() == expected, relative
subprocess.run(['python3', str(iteration / 'foreign_jobs.py')], check=True)
with (iteration / 'controller-hf32-rounding.log').open('xb') as log:
    child = subprocess.Popen(['bash', str(iteration / 'controller_hf32_rounding_diagnostic.sh')],
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', child.pid)
