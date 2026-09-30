"""Validate observed HcPre object loads against the actual build manifest."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('repo', type=Path)
parser.add_argument('manifest', type=Path)
parser.add_argument('observed', type=Path)
args = parser.parse_args()
manifest = json.loads(args.manifest.read_text())
records = [r for r in json.loads(args.observed.read_text())
           if Path(r['path']).name.startswith('HcPre_')]
assert records, 'No actual HcPre object load observed'
for row in records:
    path = Path(row['path'])
    relative = str(path.relative_to(args.repo))
    assert manifest[relative] == row['sha256']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']
print('ACTUAL_HC_PRE_KERNEL_SELECTION_PASS', records)
