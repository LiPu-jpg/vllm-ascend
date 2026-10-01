"""Verify complete diagnostic coverage and preserve every observed failure."""

import hashlib
import json
import sys
from pathlib import Path


def main():
    root = Path(sys.argv[1])
    expected = {
        f"t{tokens}-d{hidden}-signed{signed}-previousd{previous}-a{amplitude}"
        for hidden in (4103, 4104, 7168, 7169)
        for tokens in (1, 17)
        for signed in (0, 1)
        for previous, amplitude in ((hidden, 0), (hidden, 16), (8192, 0), (8192, 16))
    }
    assert len(expected) == 64
    arms, summaries = {}, {}
    for arm in ("baseline", "candidate"):
        folder = root / f"batch-comb7-state-{arm}" / "data"
        rows = json.loads((folder / "results.json").read_text())
        keyed = {row["case"]: row for row in rows}
        assert len(rows) == len(keyed) == 64 and set(keyed) == expected
        for row in rows:
            assert not row["errors"], row
            assert row["previous_outputs_finite"], row
            for name in ("history_comparison", "repeat_comparison", "graph_comparison"):
                assert len(row[name]) == 4
            tensor = folder / (row["case"] + ".pt")
            assert (
                hashlib.sha256(tensor.read_bytes()).hexdigest() == row["saved_sha256"]
            )
        groups = {}
        for row in rows:
            previous = groups.setdefault(row["target"], row["input_sha256"])
            assert previous == row["input_sha256"]
        summaries[arm] = {
            "cases": 64,
            "cpu_failed_cases": [
                row["case"] for row in rows if not row["cpu_accuracy_pass"]
            ],
            **{
                name + "_mismatches": [
                    row["case"]
                    for row in rows
                    if any(not m["byte_equal"] for m in row[name])
                ]
                for name in (
                    "history_comparison",
                    "repeat_comparison",
                    "graph_comparison",
                )
            },
        }
        arms[arm] = keyed
    assert all(
        arms["baseline"][case]["input_sha256"]
        == arms["candidate"][case]["input_sha256"]
        for case in expected
    )
    report = {
        "scope": "Completed production-plugin tail history diagnostics; no speedup claim",
        "recording_complete": True,
        "all64_input_hashes_match": True,
        "arms": summaries,
    }
    with (root / "tail-history-comparison-v1.json").open("x") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
