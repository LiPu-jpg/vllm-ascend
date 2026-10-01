"""One-shot stage four launch after completed timing and verified frozen inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path('/mnt/workspace/hc-pre-reduction-20260930')
iteration = root / 'iteration-08'
for suffix in ('pid', 'exit', 'log'):
    assert not (iteration / f'controller-v5-profile-model.{suffix}').exists(), suffix
assert (iteration / 'controller-v4-performance.exit').read_text().strip() == '0'
assert 'BATCH_COMB_ALL28_ORDERED_PERFORMANCE_CONTROLS_COMPLETE' in (
    iteration / 'controller-v4-performance.log').read_text()
for record in root.glob('iteration-*/controller*.pid'):
    try:
        words = (Path('/proc') / record.read_text().strip() / 'cmdline').read_bytes()
    except FileNotFoundError:
        continue
    assert str(root).encode() not in words, f'Own controller live: {record}'
for manifest in ('frozen-input-sha256.json', 'validation-input-sha256.json', 'hf32-reference-input-sha256.json', 'performance-input-sha256.json', 'profile-model-input-sha256.json', 'shared-validation-input-sha256.json'):
    for relative, expected in json.loads((iteration / manifest).read_text()).items():
        assert hashlib.sha256((iteration / relative).read_bytes()).hexdigest() == expected, relative
refs = json.loads((iteration / 'revisions.json').read_text())
for variant, expected in refs.items():
    repo = root / f'batch-comb-source-{variant}'
    actual = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == expected, (variant, actual)
    subprocess.run(['git', '-C', str(repo), 'diff', '--exit-code'], check=True)
subprocess.run(['python3', str(iteration / 'verify_shared_validation_dependencies.py')], check=True)
subprocess.run(['python', str(iteration / 'foreign_jobs.py')], check=True)
with (iteration / 'controller-v5-profile-model.log').open('xb') as log:
    child = subprocess.Popen(['bash', str(iteration / 'controller_profile_model.sh')],
        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
print('STARTED_PID', child.pid)
