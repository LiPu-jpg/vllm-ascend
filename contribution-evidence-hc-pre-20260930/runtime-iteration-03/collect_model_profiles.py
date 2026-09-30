"""Snapshot completed full-model profiles; include trace evidence and failures."""
import hashlib
from pathlib import Path
import tarfile

root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-03')
archive = root / 'actual-model-profiles-v1.tar'
assert not archive.exists(), 'Do not replace an evidence snapshot'
files = []
for variant in ('baseline', 'candidate'):
    folder = root / f'optional5-model-graph-{variant}'
    assert (folder / 'run.exit').read_text().strip() == '0', folder
    assert len(list(folder.rglob('trace_view.json'))) == 1, folder
    files.extend(path for path in folder.rglob('*')
                 if path.is_file() and path.suffix in ('.json', '.csv', '.log', '.txt', '.exit'))
with tarfile.open(archive, 'w') as tar:
    for path in sorted(files):
        tar.add(path, arcname=str(path.relative_to(root)))
print('ACTUAL_MODEL_SNAPSHOT', archive.stat().st_size,
      hashlib.sha256(archive.read_bytes()).hexdigest(), len(files))
