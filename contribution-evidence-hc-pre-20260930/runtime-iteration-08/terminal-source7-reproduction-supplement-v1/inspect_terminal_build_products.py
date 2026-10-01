"""Verify completed products while retaining the original controller/guard outcome.

This is an integrity inspection, not permission to run NPU work. A failed
post-build guard still requires a fresh idle window before validation.
"""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path('/mnt/workspace/hc-pre-reduction-20260930')
iteration = root / 'iteration-08'
status = (iteration / 'controller-v1.exit').read_text().strip()
pid = (iteration / 'controller-v1.pid').read_text().strip()
try:
    words = (Path('/proc') / pid / 'cmdline').read_bytes()
except FileNotFoundError:
    words = b''
assert str(iteration / 'controller_v1.sh').encode() not in words, 'Build still live'
log = (iteration / 'controller-v1.log').read_text()
refs = json.loads((iteration / 'revisions.json').read_text())
report = {'scope': 'Terminal build integrity; does not override any guard failure',
          'controller_pid': int(pid), 'controller_exit': status,
          'completion_marker': 'BATCH_COMB_MATCHED_BUILDS_COMPLETE' in log,
          'variants': {}}
for relative, expected in json.loads((iteration / 'frozen-input-sha256.json').read_text()).items():
    assert hashlib.sha256((iteration / relative).read_bytes()).hexdigest() == expected, relative
for variant, expected in refs.items():
    source = root / f'batch-comb-source-{variant}'
    actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == expected
    subprocess.run(['git', '-C', str(source), 'diff', '--exit-code'], check=True)
    assert f'MATCHED_NATIVE_AND_OPP_BUILD_PASS {variant} {expected}' in log
    manifest = json.loads((iteration / f'full-extension-build-{variant}' / 'binary-sha256.json').read_text())
    assert len(manifest) >= 4
    assert sum(name.endswith('.so') for name in manifest) == 2
    assert any('HcPre_' in name and name.endswith('.o') for name in manifest)
    for relative, expected_hash in manifest.items():
        assert hashlib.sha256((source / relative).read_bytes()).hexdigest() == expected_hash, relative
    report['variants'][variant] = {'source_head': actual, 'verified_binary_sha256': manifest}
guard = iteration / 'foreign-after-build.json'
report['foreign_after_build'] = json.loads(guard.read_text()) if guard.exists() else None
report['npu_after_build_snapshot_exists'] = (iteration / 'npu-after-build.txt').exists()
(iteration / 'terminal-build-integrity.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
