import hashlib
import tarfile
from pathlib import Path

root = Path('/mnt/workspace/hc-pre-reduction-20260930')
assert (root / 'full-graph.exit').read_text().strip() == '0'
assert (root / 'full-operator-v5/run.exit').read_text().strip() == '0'
archive = root / 'full-validation-text-v5.tar.gz'
names = [
    'full-plugin-v1', 'full-plugin-v2', 'full-plugin-v3',
    'full-operator-v4', 'full-operator-v5',
    'full-graph-candidate-a', 'full-graph-candidate-b', 'full-graph-baseline-b',
    'full-validation-analysis', 'full-graph.exit',
    'run_full_plugin.sh', 'run_full_plugin_v2.sh', 'run_full_plugin_v3.sh',
    'run_full_operator_v4.sh', 'run_full_operator_v5.sh',
    'full_operator_runner.py', 'measure_full_graph.sh', 'analyze_full_graph.py',
    'archive_full_validation.py',
]
names.extend(p.name for p in root.glob('full-*-controller.log'))
names.extend(p.name for p in root.glob('full-*-controller.pid'))
with tarfile.open(archive, 'w:gz') as out:
    for name in names:
        path = root / name
        files = sorted(path.rglob('*')) if path.is_dir() else [path]
        for file in files:
            if file.is_file() and file.suffix != '.pt':
                out.add(file, arcname=str(file.relative_to(root)), recursive=False)
    for name in [
        'benchmarks/hc_pre.py',
        'tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py',
    ]:
        out.add(root / 'full-plugin-source-v2' / name, arcname='source/' + name)
print('SHA256', hashlib.sha256(archive.read_bytes()).hexdigest(), 'bytes', archive.stat().st_size)
