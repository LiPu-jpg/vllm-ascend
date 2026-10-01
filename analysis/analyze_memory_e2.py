"""Audit every frozen-input allocator observation across original, E1 and E2."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    reports = {
        variant: json.loads((args.results / f"memory-{variant}.json").read_text())
        for variant in ["control", "launch_only", "candidate"]
    }
    for report in reports.values():
        assert report["complete"] and report["all_passed"] and len(report["rows"]) == 32
    assert len({report["pid"] for report in reports.values()}) == 3
    assert len({report["script_sha256"] for report in reports.values()}) == 1
    rows = []
    for i in range(32):
        records = {variant: report["rows"][i] for variant, report in reports.items()}
        source = records["control"]
        for key in ["case", "order", "return_lse", "input_sha256", "capture_sha256"]:
            assert all(record[key] == source[key] for record in records.values()), (
                i,
                key,
            )
        assert all(record["status"] == "passed" for record in records.values())
        observations = {
            variant: record["allocator_observations"]
            for variant, record in records.items()
        }
        comparisons = {}
        for mode in ["eager", "graph"]:
            values = {
                variant: record[mode]["peak_increase_bytes"]
                for variant, record in observations.items()
            }
            assert all(value >= 0 for value in values.values())
            comparisons[mode] = dict(
                peak_increase_bytes=values,
                original_to_candidate_reduction_bytes=values["control"]
                - values["candidate"],
                launch_only_to_candidate_reduction_bytes=values["launch_only"]
                - values["candidate"],
                original_to_launch_only_reduction_bytes=values["control"]
                - values["launch_only"],
            )
        rows.append(
            dict(
                case=source["case"],
                order=source["order"],
                return_lse=source["return_lse"],
                input_sha256=source["input_sha256"],
                capture_sha256=source["capture_sha256"],
                observations=observations,
                comparisons=comparisons,
            )
        )
    groups = {}
    for count in [1, 32]:
        selected = [row for row in rows if int(row["case"].rsplit("-", 1)[1]) == count]
        assert len(selected) == 16
        groups[str(count)] = {}
        for mode in ["eager", "graph"]:
            changes = [
                row["comparisons"][mode]["original_to_candidate_reduction_bytes"]
                for row in selected
            ]
            groups[str(count)][mode] = dict(
                cases=len(selected),
                min_reduction_bytes=min(changes),
                max_reduction_bytes=max(changes),
                lower=sum(change > 0 for change in changes),
                unchanged=sum(change == 0 for change in changes),
                higher=sum(change < 0 for change in changes),
            )
    report = dict(
        complete=True,
        rows=rows,
        groups=groups,
        script_pids={variant: item["pid"] for variant, item in reports.items()},
        scope="Torch allocator peak-increase observations on frozen SFA inputs. Not logical workspace bytes, device-wide HBM, model memory savings or latency. All live/peak/reserved observations and unchanged/worse cases retained.",
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(groups, indent=2))


if __name__ == "__main__":
    main()
