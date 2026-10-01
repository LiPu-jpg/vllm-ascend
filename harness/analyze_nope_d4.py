"""Audit all balanced NoPE samples, keeping production calls and controls separate."""

import argparse
import json
import math
import statistics
from pathlib import Path


def summarize(rows):
    assert rows
    return dict(
        cases=len(rows),
        lower=sum(r["change_percent"] < 0 for r in rows),
        higher=sum(r["change_percent"] > 0 for r in rows),
        best_change_percent=min(r["change_percent"] for r in rows),
        worst_change_percent=max(r["change_percent"] for r in rows),
        geometric_mean_time_change_percent=(
            math.exp(statistics.mean(math.log(r["candidate_us"] / r["baseline_us"]) for r in rows)) - 1
        )
        * 100,
        separated_lower=sum(r["separated_lower"] for r in rows),
        separated_higher=sum(r["separated_higher"] for r in rows),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    labels = ["b1", "c1", "c2", "b2"]
    runs = [json.loads((args.results / f"nope-{label}.json").read_text()) for label in labels]
    assert all(r["complete"] and r["all_passed"] and len(r["rows"]) == 32 for r in runs)
    assert len({r["metadata"]["pid"] for r in runs}) == 4
    for key in ["script_sha256", "paired_sha256", "caller_provenance", "device", "torch_version", "torch_npu_version"]:
        assert all(r["metadata"][key] == runs[0]["metadata"][key] for r in runs), key
    records = []
    for index in range(32):
        source = [r["rows"][index] for r in runs]
        for key in ["case", "order", "return_lse", "input_sha256", "capture_sha256"]:
            assert all(r[key] == source[0][key] for r in source), (index, key)
        assert all(r["status"] == "passed" and r["numerical_reference"] for r in source)
        samples = [r["graph_device_us"] for r in source]
        assert all(len(s) == 5 and all(math.isfinite(v) and v > 0 for v in s) for s in samples)
        medians = [statistics.median(s) for s in samples]
        b, c = statistics.median(samples[0] + samples[3]), statistics.median(samples[1] + samples[2])
        records.append(
            dict(
                index=index,
                case=source[0]["case"],
                order=source[0]["order"],
                return_lse=source[0]["return_lse"],
                input_sha256=source[0]["input_sha256"],
                capture_sha256=source[0]["capture_sha256"],
                query_count=int(source[0]["case"].rsplit("-", 1)[1]),
                baseline_us=b,
                candidate_us=c,
                change_percent=(c / b - 1) * 100,
                process_medians_us=dict(zip(labels, medians)),
                separated_lower=max(medians[1:3]) < min(medians[0], medians[3]),
                separated_higher=min(medians[1:3]) > max(medians[0], medians[3]),
                raw_device_us=dict(zip(labels, samples)),
                raw_wall_us={label: row["eager_batch_wall_us"] for label, row in zip(labels, source)},
            )
        )
    groups = {}
    for count in [1, 32]:
        for order in ["indexer", "chronological"]:
            for lse in [False, True]:
                selected = [
                    r for r in records if r["query_count"] == count and r["order"] == order and r["return_lse"] == lse
                ]
                assert len(selected) == 4
                groups[f"q{count}-{order}-lse{lse}"] = summarize(selected)
    report = dict(
        complete=True,
        rows=records,
        groups=groups,
        process_pids=dict(zip(labels, [r["metadata"]["pid"] for r in runs])),
        scope="Isolated SFA operator on frozen Indexer outputs with synthetic features. No model speedup claim.",
        interpretation="Process-range separation is descriptive, not a significance test. Every slowdown is retained.",
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(groups, indent=2))


if __name__ == "__main__":
    main()
