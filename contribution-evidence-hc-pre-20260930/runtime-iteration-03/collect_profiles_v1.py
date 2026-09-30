"""Archive terminal operator profiles; do not include live model phases."""
import hashlib
from pathlib import Path
import tarfile

root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-03')
archive = root / 'operator-profiles-v1.tar'
assert not archive.exists()
files = []
for mode in ('eager', 'graph'):
    for variant in ('baseline', 'candidate'):
        folder = root / f'optional3-profile-{mode}-{variant}'
        assert (folder / 'run.exit').read_text().strip() == '0', folder
        files.extend(path for path in folder.rglob('*')
                     if path.is_file() and path.suffix in ('.csv', '.json', '.log', '.txt', '.exit'))
with tarfile.open(archive, 'w') as tar:
    for path in sorted(files):
        tar.add(path, arcname=str(path.relative_to(root)))
print('PROFILE_SNAPSHOT', archive.stat().st_size, hashlib.sha256(archive.read_bytes()).hexdigest(), len(files))
