"""Compare saved production-baseline tensors; this does not execute on NPU."""

import argparse
import hashlib
import json
from pathlib import Path

import torch


def equal_bytes(left, right):
    return torch.equal(
        left.contiguous().view(torch.uint8), right.contiguous().view(torch.uint8)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    torch.set_num_threads(1)
    rows = []
    records = {
        name: {
            row["case"]: row
            for row in json.loads((folder / "data/results.json").read_text())
        }
        for name, folder in (("old", args.old), ("new", args.new))
    }
    assert len(records["old"]) == len(records["new"]) == 60
    assert set(records["old"]) == set(records["new"])
    source_heads = [
        (folder / "source-head.txt").read_text().strip()
        for folder in (args.old, args.new)
    ]
    assert source_heads == ["62e05feb3db521230c27714ad4347bd0d9d38f1a"] * 2
    for case in sorted(records["old"]):
        old_row, new_row = (records[arm][case] for arm in ("old", "new"))
        assert old_row["input_sha256"] == new_row["input_sha256"], case
        tensors = []
        for folder, record in ((args.old, old_row), (args.new, new_row)):
            path = folder / "data" / f"{case}.pt"
            assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], (
                path
            )
            tensors.append(torch.load(path, weights_only=True))
        old, new = tensors
        assert len(old["expected"]) == len(new["expected"])
        assert all(
            equal_bytes(a, b)
            for a, b in zip(old["expected"], new["expected"], strict=True)
        ), case
        metrics = []
        for api in ("v2", "v3"):
            for index, (a, b) in enumerate(zip(old[api], new[api], strict=True)):
                assert a.shape == b.shape and a.dtype == b.dtype
                finite = torch.isfinite(a) & torch.isfinite(b)
                differences = (a.float() - b.float()).abs()[finite]
                metrics.append(
                    {
                        "api": api,
                        "output": index,
                        "byte_equal": equal_bytes(a, b),
                        "different_value_count": int((a != b).sum()),
                        "old_nonfinite_count": int((~torch.isfinite(a)).sum()),
                        "new_nonfinite_count": int((~torch.isfinite(b)).sum()),
                        "max_finite_absolute_difference": float(differences.max())
                        if differences.numel()
                        else None,
                    }
                )
        rows.append(
            {
                "case": case,
                "inputs_and_cpu_expected_byte_equal": True,
                "old_cpu_accuracy_pass": old_row["cpu_accuracy_pass"],
                "new_cpu_accuracy_pass": new_row["cpu_accuracy_pass"],
                "all_npu_output_bytes_equal": all(m["byte_equal"] for m in metrics),
                "output_metrics": metrics,
            }
        )
    report = {
        "scope": "CPU analysis of saved baseline tensors from two completed production NPU runs; no new NPU execution or performance claim",
        "source_heads": source_heads,
        "old_directory": str(args.old),
        "new_directory": str(args.new),
        "cases": rows,
        "byte_mismatch_cases": [
            r["case"] for r in rows if not r["all_npu_output_bytes_equal"]
        ],
    }
    args.output.mkdir(exist_ok=False)
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print("SAVED_BASELINE_INPUTS_AND_EXPECTED_MATCH", len(rows), flush=True)
    print(
        "BASELINE_CROSS_PROCESS_BYTE_MISMATCHES",
        report["byte_mismatch_cases"],
        flush=True,
    )


if __name__ == "__main__":
    main()
