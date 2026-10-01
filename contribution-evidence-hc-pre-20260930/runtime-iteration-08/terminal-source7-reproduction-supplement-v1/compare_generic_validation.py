"""Require complete cases and baseline parity while retaining CPU failures."""

import json
import sys
from pathlib import Path


def main():
    iteration = Path(sys.argv[1])
    arms = {
        variant: json.loads(
            (
                iteration / f"batch-comb3-generic-{variant}" / "data/results.json"
            ).read_text()
        )
        for variant in ("baseline", "candidate")
    }
    assert all(len(rows) == 24 for rows in arms.values())
    expected_cases = {
        f"hc{width}-t{tokens}-signed{signed}-i{iters}"
        for width in (1, 3, 8)
        for tokens in (1, 17)
        for signed in (0, 1)
        for iters in (1, 3)
    }
    keyed = {arm: {row["case"]: row for row in rows} for arm, rows in arms.items()}
    assert all(set(rows) == expected_cases for rows in keyed.values())
    defects = []
    for case in sorted(expected_cases):
        baseline, candidate = (keyed[arm][case] for arm in ("baseline", "candidate"))
        for arm, row in (("baseline", baseline), ("candidate", candidate)):
            if row["errors"]:
                defects.append({"arm": arm, "case": case, "errors": row["errors"]})
        if baseline["input_sha256"] != candidate["input_sha256"]:
            defects.append({"case": case, "error": "input digest mismatch"})
        if baseline["cpu_accuracy_pass"] != candidate["cpu_accuracy_pass"]:
            defects.append({"case": case, "error": "CPU pass bitmap mismatch"})
    summary = {
        "scope": "Generic-width correctness recording; no performance claim",
        "cases_per_arm": 24,
        "cpu_failed_cases": {
            arm: [row["case"] for row in rows if not row["cpu_accuracy_pass"]]
            for arm, rows in arms.items()
        },
        "defects": defects,
        "parity_and_recording_complete": not defects,
        "all_cpu_cases_passed": all(
            row["cpu_accuracy_pass"] for rows in arms.values() for row in rows
        ),
    }
    (iteration / "generic-width-comparison.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))
    assert not defects, defects


if __name__ == "__main__":
    main()
