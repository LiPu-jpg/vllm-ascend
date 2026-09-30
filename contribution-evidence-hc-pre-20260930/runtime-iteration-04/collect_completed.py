"""Snapshot all terminal Cast validation text, including failing boundaries."""
import hashlib
from pathlib import Path
import tarfile

root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-04')
archive = root / 'completed-text-v1.tar.gz'
assert not archive.exists(), 'Never overwrite a completed evidence snapshot'
for i in (1, 2, 3):
    assert (root / f'controller-v{i}.exit').read_text().strip() == '0'
files = []
for folder in sorted(root.glob('cast*-*')):
    if not folder.is_dir():
        continue
    status = (folder / 'run.exit').read_text().strip()
    assert status == '0' or ('boundary' in folder.name and status == '1'), folder
    files.extend(p for p in folder.rglob('*') if p.is_file() and not p.is_symlink()
                 and p.suffix in ('.json', '.csv', '.log', '.txt', '.exit', '.xml', '.tsv', '.py'))
files.extend(p for p in root.glob('controller-v*') if p.is_file())
with tarfile.open(archive, 'w:gz') as tar:
    for path in sorted(files):
        tar.add(path, arcname=str(path.relative_to(root)))
print('COMPLETED_SNAPSHOT', archive.stat().st_size,
      hashlib.sha256(archive.read_bytes()).hexdigest(), len(files))
