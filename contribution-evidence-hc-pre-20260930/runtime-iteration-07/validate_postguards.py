"""Retained numerical failure never bypasses the foreign/device postguards."""
import json
from pathlib import Path
import sys
folder = Path(sys.argv[1])
statuses = json.loads((folder / 'guards-after-status.json').read_text())
assert set(statuses) == {'npu_query', 'npu_idle', 'other_jobs', 'foreign_jobs'}
assert all(code == 0 for code in statuses.values()), statuses
assert json.loads((folder / 'foreign-before.json').read_text()) == []
assert json.loads((folder / 'foreign-after.json').read_text()) == []
for name in ('npu-before.txt', 'npu-after.txt'):
    assert 'No running processes' in (folder / name).read_text()
