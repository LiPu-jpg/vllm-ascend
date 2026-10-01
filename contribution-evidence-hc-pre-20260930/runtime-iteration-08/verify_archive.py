"""Verify immutable archive bytes, without claiming any numerical or timing pass."""

import hashlib
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    records = json.loads((root / 'archive-sha256.json').read_text())
    actual = {str(p.relative_to(root)) for p in root.rglob('*')
              if p.is_file() and p.name != 'archive-sha256.json'}
    assert actual == set(records), (actual - set(records), set(records) - actual)
    for name, digest in records.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    print('ARCHIVE_BYTES_VERIFIED', len(records))
    print('INTEGRITY_ONLY;_NUMERICAL_FAILURES_AND_UNEXECUTED_PHASES_REMAIN')


if __name__ == '__main__':
    main()
