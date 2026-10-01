"""Verify task-owned dependencies imported from earlier iteration directories."""

import hashlib
import json
from pathlib import Path


def main():
    iteration = Path(__file__).resolve().parent
    root = iteration.parent
    manifest = json.loads(
        (iteration / "shared-validation-dependency-sha256.json").read_text()
    )
    verified = {}
    for relative, expected in manifest.items():
        actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
        assert actual == expected, (relative, actual, expected)
        verified[relative] = actual
    print(
        json.dumps(
            {
                "scope": "Shared task-owned validation dependencies only",
                "verified": verified,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
