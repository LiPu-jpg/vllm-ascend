"""Verify every published text artifact; this does not verify numerical/performance claims."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = root / 'archive-sha256.json'
data = json.loads(manifest.read_text())
assert data['algorithm'] == 'sha256'
expected = {item['path']: item['sha256'] for item in data['files']}
assert len(expected) == len(data['files'])
actual = {
    str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in root.rglob('*') if path.is_file() and path != manifest
}
assert actual == expected, 'Missing, extra or changed archive files'
print('ARCHIVE_TEXT_SHA256_PASS', len(expected))
