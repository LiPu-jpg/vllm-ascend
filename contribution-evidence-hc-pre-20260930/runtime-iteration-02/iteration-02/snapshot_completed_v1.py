"""Snapshot terminal experiment evidence; explicitly omit live partial phases."""
import hashlib
import json
from pathlib import Path
import tarfile

task = Path('/mnt/workspace/hc-pre-reduction-20260930')
root = task / 'iteration-02'
public = []
manifest = []
suffixes = {'.log', '.txt', '.csv', '.xml', '.json', '.exit', '.tsv'}
for iteration, prefix in ((task / 'iteration-01', 'v4-'), (root, '')):
    for child in iteration.iterdir():
        if not child.is_dir() or not child.name.startswith(prefix) or not (child / 'run.exit').exists():
            continue
        for path in sorted(child.rglob('*')):
            if not path.is_file():
                continue
            relative = str(path.relative_to(task))
            manifest.append({'path': relative, 'bytes': path.stat().st_size,
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            if path.suffix in suffixes and path.name != 'trace_view.json':
                public.append(path)
for path in root.iterdir():
    if path.is_file() and path.suffix in suffixes | {'.py', '.sh', '.patch', '.c'}:
        public.append(path)
build = root / 'full-extension-build-v3'
for name in ('commands.json', 'binary-sha256.json', 'compile_commands.json', 'CMakeCache.txt'):
    path = build / name
    if path.exists():
        public.append(path)
metadata = root / 'completed-snapshot-v1-manifest.json'
metadata.write_text(json.dumps(manifest, indent=2))
public.append(metadata)
archive = root / 'completed-snapshot-v1.tar'
assert not archive.exists(), 'Use a new name; never overwrite a snapshot'
with tarfile.open(archive, 'w') as tar:
    for path in sorted(set(public)):
        tar.add(path, arcname=str(path.relative_to(task)))
print('SNAPSHOT', archive.stat().st_size, hashlib.sha256(archive.read_bytes()).hexdigest(), len(public))
