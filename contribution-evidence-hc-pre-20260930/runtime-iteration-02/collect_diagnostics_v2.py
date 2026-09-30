"""Archive completed new diagnostics without modifying any experiment result."""
import hashlib
import json
from pathlib import Path
import tarfile

task = Path('/mnt/workspace/hc-pre-reduction-20260930')
root = task / 'iteration-02'
paths = []
manifest = []
suffixes = {'.log', '.txt', '.csv', '.xml', '.json', '.exit', '.tsv'}
for folder, prefixes in ((root, ('exact3-', 'queued1-', 'model-profile1-')),
                         (task / 'iteration-01', ('exact3-profile-',))):
    for child in sorted(folder.iterdir()):
        if not child.is_dir() or not child.name.startswith(prefixes):
            continue
        assert (child / 'run.exit').exists(), child
        for path in sorted(child.rglob('*')):
            if not path.is_file():
                continue
            manifest.append({'path': str(path.relative_to(task)), 'bytes': path.stat().st_size,
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            if path.suffix in suffixes and path.name != 'trace_view.json':
                paths.append(path)
        # Model traces are required to verify graph execution.
        if child.name.startswith('model-profile1-'):
            paths.extend(child.rglob('trace_view.json'))
archive = root / 'completed-diagnostics-v2.tar'
assert not archive.exists(), archive
metadata = root / 'completed-diagnostics-v2-manifest.json'
assert not metadata.exists(), metadata
metadata.write_text(json.dumps(manifest, indent=2))
paths.append(metadata)
with tarfile.open(archive, 'w') as tar:
    for path in sorted(set(paths)):
        tar.add(path, arcname=str(path.relative_to(task)))
print('SNAPSHOT', archive.stat().st_size, hashlib.sha256(archive.read_bytes()).hexdigest(), len(paths))
