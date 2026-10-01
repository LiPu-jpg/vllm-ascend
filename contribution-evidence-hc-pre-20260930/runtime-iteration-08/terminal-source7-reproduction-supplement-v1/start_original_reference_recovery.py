"""Start correctness recording once; numerical failures remain explicit."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path('/mnt/workspace/hc-pre-reduction-20260930')
iteration = root / 'iteration-08'
assert (iteration / 'controller-v1.exit').exists(), 'Build is not terminal'
assert (iteration / 'controller-v2.exit').read_text().strip() == '1', 'Keep original failed controller outcome'
assert not (iteration / 'batch-comb1-benchmark-fixture-candidate/data/results.json').exists(), 'Unexpected execution state'
assert json.loads((iteration / 'batch-comb1-benchmark-fixture-candidate/guards-after-status.json').read_text())['foreign_jobs'] == 1
for suffix in ('pid', 'exit', 'log'):
    assert not (iteration / f'controller-v2r-original-reference.{suffix}').exists(), suffix
for record in root.glob('iteration-*/controller*.pid'):
    try:
        words = (Path('/proc') / record.read_text().strip() / 'cmdline').read_bytes()
    except FileNotFoundError:
        continue
    assert str(root).encode() not in words, f'Own controller still live: {record}'
for manifest in ('frozen-input-sha256.json', 'validation-input-sha256.json',
                 'shared-validation-input-sha256.json', 'original-reference-recovery-input-sha256.json'):
    for relative, expected in json.loads((iteration / manifest).read_text()).items():
        assert hashlib.sha256((iteration / relative).read_bytes()).hexdigest() == expected, relative
subprocess.run(['python3', str(iteration / 'inspect_terminal_build_products.py')], check=True)
subprocess.run(['python3', str(iteration / 'verify_shared_validation_dependencies.py')], check=True)
subprocess.run(['python3', str(iteration / 'foreign_jobs.py')], check=True)
with (iteration / 'controller-v2r-original-reference.log').open('xb') as log:
    child = subprocess.Popen(['bash', str(iteration / 'controller_original_reference_recovery.sh')],
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', child.pid)
