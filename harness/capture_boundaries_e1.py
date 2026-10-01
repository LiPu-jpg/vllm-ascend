"""Capture additional actual Indexer outputs once using the full original runtime."""

import argparse
import hashlib
import json
from pathlib import Path

import indexer_sfa_v2 as indexer
import torch
import torch_npu  # noqa: F401
from experiment import guard


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["baseline"], required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    args.reference.mkdir(parents=True, exist_ok=True)
    assert indexer.test.enable_custom_op()
    rows = []
    for quantized in [False, True]:
        for dtype in [torch.float16, torch.bfloat16]:
            for count in [2, 4, 9, 10, 11, 12, 13, 16, 19, 20, 21, 24]:
                guard()
                label = f"{'quant' if quantized else 'native'}-{dtype}-{count}"
                target = args.reference / f"{label}-inputs.pt"
                try:
                    assert not target.exists()
                    cpu = indexer.capture(dtype, count, quantized)
                    torch.save(cpu, target)
                    row = dict(
                        case=label, status="passed", input_file_sha256=hashlib.sha256(target.read_bytes()).hexdigest()
                    )
                except Exception as exc:
                    row = dict(case=label, status="failed", error=repr(exc))
                rows.append(row)
                args.output.write_text(json.dumps(dict(complete=False, rows=rows), indent=2) + "\n")
                print(json.dumps(row), flush=True)
    guard()
    passed = len(rows) == 48 and all(r["status"] == "passed" for r in rows)
    report = dict(
        complete=True,
        all_passed=passed,
        rows=rows,
        indexer_script_sha256=hashlib.sha256(Path(indexer.__file__).read_bytes()).hexdigest(),
        helper_sha256=hashlib.sha256(Path(indexer.test.__file__).read_bytes()).hexdigest(),
        scope="actual native/quantized Indexer order with synthetic features; not a model distribution",
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
