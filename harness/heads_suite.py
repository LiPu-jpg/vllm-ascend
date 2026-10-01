"""Run the complete new and retained NPU regression files and count cases."""

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from experiment import guard


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["baseline", "candidate"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--junitxml", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists() and not args.junitxml.exists()
    root = Path(__file__).parent / "ops_cases_v2"
    guard()
    status = pytest.main(
        [
            "-q",
            "--tb=short",
            f"--junitxml={args.junitxml}",
            str(root / "test_sparse_flash_attention_active_cores.py"),
            str(root / "test_sparse_flash_attention_active_workspace.py"),
            str(root / "test_sparse_flash_attention_sparse_indices.py"),
        ]
    )
    guard()
    tree = ET.parse(args.junitxml)
    cases = list(tree.getroot().iter("testcase"))
    failures = sum(bool(list(case.iter("failure"))) or bool(list(case.iter("error"))) for case in cases)
    skipped = sum(bool(list(case.iter("skipped"))) for case in cases)
    args.output.write_text(
        json.dumps(
            dict(
                variant=args.variant,
                complete=True,
                exit_code=int(status),
                cases=len(cases),
                failures=failures,
                skipped=skipped,
            ),
            indent=2,
        )
        + "\n"
    )
    if status == 0:
        assert len(cases) == 616 and failures == skipped == 0
    raise SystemExit(int(status))


if __name__ == "__main__":
    main()
