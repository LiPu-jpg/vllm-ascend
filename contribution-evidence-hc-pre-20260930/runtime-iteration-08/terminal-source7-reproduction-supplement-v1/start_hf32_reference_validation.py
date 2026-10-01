"""Record corrected-reference results separately after original results finish."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path('/mnt/workspace/hc-pre-reduction-20260930')
iteration = root / 'iteration-08'
assert (iteration / 'controller-v2.exit').read_text().strip() == '1'
assert (iteration / 'controller-v2r-original-reference.exit').read_text().strip() == '0'
assert 'BATCH_COMB_ORIGINAL_REFERENCE_RECOVERY_RESULTS_RECORDED_WITH_FAILURES' in (
    iteration / 'controller-v2r-original-reference.log').read_text()
for suffix in ('pid', 'exit', 'log'):
    assert not (iteration / f'controller-v3-hf32-reference.{suffix}').exists(), suffix
for record in root.glob('iteration-*/controller*.pid'):
    try:
        words = (Path('/proc') / record.read_text().strip() / 'cmdline').read_bytes()
    except FileNotFoundError:
        continue
    assert str(root).encode() not in words, f'Own controller still live: {record}'
for manifest in ('frozen-input-sha256.json', 'validation-input-sha256.json',
                 'hf32-reference-input-sha256.json', 'shared-validation-input-sha256.json',
                 'original-reference-recovery-input-sha256.json'):
    for relative, expected in json.loads((iteration / manifest).read_text()).items():
        assert hashlib.sha256((iteration / relative).read_bytes()).hexdigest() == expected, relative
subprocess.run(['python3', str(iteration / 'inspect_terminal_build_products.py')], check=True)
subprocess.run(['python3', str(iteration / 'verify_shared_validation_dependencies.py')], check=True)
subprocess.run(['python3', str(iteration / 'foreign_jobs.py')], check=True)
with (iteration / 'controller-v3-hf32-reference.log').open('xb') as log:
    child = subprocess.Popen(['bash', str(iteration / 'controller_hf32_reference.sh')],
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', child.pid)
