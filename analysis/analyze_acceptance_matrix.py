"""Compare every retained SFA matrix case; refuse incomplete or mismatched runs."""

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path


DATASETS = {"paired": 52, "unsorted": 52, "indexer": 16, "page48": 52}
LABELS = ("b1", "c1", "c2", "b2")
IDENTITY_KEYS = (
    "cases_sha256", "test_sha256", "script_sha256", "paired_sha256",
    "device", "torch_version", "torch_npu_version",
)


def require(condition, context):
    if not condition:
        raise ValueError(context)


def summarize(rows):
    ratios = [r["candidate_us"] / r["baseline_us"] for r in rows]
    return dict(
        cases=len(rows),
        lower=sum(v < 1 for v in ratios),
        unchanged=sum(v == 1 for v in ratios),
        higher=sum(v > 1 for v in ratios),
        best_change_percent=(min(ratios) - 1) * 100,
        worst_change_percent=(max(ratios) - 1) * 100,
        geometric_mean_time_change_percent=(
            math.exp(statistics.mean(math.log(v) for v in ratios)) - 1
        ) * 100,
        separated_lower=sum(r["separated_lower"] for r in rows),
        separated_higher=sum(r["separated_higher"] for r in rows),
    )


def analyze_dataset(results, dataset, expected):
    runs, hashes = {}, {}
    for label in LABELS:
        path = results / f"{dataset}-{label}.json"
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        run = json.loads(path.read_text())
        require(run["complete"] and len(run["rows"]) == expected, (dataset, label, "completion/count"))
        require(run.get("all_passed", True), (dataset, label, "failed cases"))
        require(run["metadata"]["variant"] == ("baseline" if label.startswith("b") else "candidate"),
                (dataset, label, "variant"))
        runs[label] = run
    pids = {label: run["metadata"].get("pid") for label, run in runs.items()}
    if all(pid is not None for pid in pids.values()):
        require(len(set(pids.values())) == 4, (dataset, "independent processes"))
    for key in IDENTITY_KEYS:
        values = [r["metadata"].get(key) for r in runs.values()]
        require(all(v == values[0] for v in values), (dataset, key, values))
    require(runs["b1"]["metadata"].get("script_sha256"), (dataset, "script identity missing"))
    records = []
    for index in range(expected):
        source = {label: r["rows"][index] for label, r in runs.items()}
        first = source["b1"]
        for key in ("case", "index", "order", "dtype", "rope_dim", "query_shape", "selected_counts", "input_sha256"):
            require(all(row.get(key) == first.get(key) for row in source.values()), (dataset, index, key))
        require(first.get("input_sha256"), (dataset, index, "input identity missing"))
        for label, row in source.items():
            require(row.get("status", "passed") == "passed", (dataset, index, label, "status"))
            for key in ("nonempty_reference", "bytewise_reference"):
                if key in row:
                    require(row[key] == "passed", (dataset, index, label, key, row[key]))
            samples = row["graph_device_us"]
            require(len(samples) == 5 and all(math.isfinite(v) and v > 0 for v in samples),
                    (dataset, index, label, "device samples"))
            wall = row["eager_batch_wall_us"]
            require(len(wall) == 5 and all(math.isfinite(v) and v > 0 for v in wall),
                    (dataset, index, label, "wall samples"))
        samples = {label: row["graph_device_us"] for label, row in source.items()}
        medians = {label: statistics.median(values) for label, values in samples.items()}
        baseline = statistics.median(samples["b1"] + samples["b2"])
        candidate = statistics.median(samples["c1"] + samples["c2"])
        records.append(dict(
            dataset=dataset, index=index,
            case={key: first[key] for key in ("case", "order", "dtype", "rope_dim", "query_shape", "selected_counts") if key in first},
            input_sha256=first["input_sha256"],
            baseline_us=baseline, candidate_us=candidate,
            change_percent=(candidate / baseline - 1) * 100,
            process_medians_us=medians,
            separated_lower=max(medians["c1"], medians["c2"]) < min(medians["b1"], medians["b2"]),
            separated_higher=min(medians["c1"], medians["c2"]) > max(medians["b1"], medians["b2"]),
            raw_device_us=samples,
            raw_wall_us={label: row["eager_batch_wall_us"] for label, row in source.items()},
            reference_checks={label: {key: row[key] for key in ("status", "nonempty_reference", "bytewise_reference") if key in row}
                              for label, row in source.items()},
        ))
    return records, hashes, pids


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--order", choices=("B/C/C/B", "C/B/B/C"), default="B/C/C/B")
    args = parser.parse_args()
    require(not args.output.exists(), "Use a fresh output directory to retain earlier results.")
    args.output.mkdir(parents=True)
    report = dict(complete=False, order=args.order, rows=[], datasets={}, input_files_sha256={}, process_pids={},
                  scope="Isolated SFA on one physical A2; no model speedup claim.",
                  interpretation="All 172 cases retained, including controls and slowdowns. Process-range separation is descriptive, not statistical significance.")
    try:
        for dataset, count in DATASETS.items():
            rows, hashes, pids = analyze_dataset(args.results, dataset, count)
            report["rows"].extend(rows)
            report["datasets"][dataset] = summarize(rows)
            report["input_files_sha256"].update(hashes)
            report["process_pids"][dataset] = pids
        require(len(report["rows"]) == 172, "Total case count")
        report.update(complete=True, summary=summarize(report["rows"]),
                      metadata_pid_verified={dataset: all(pid is not None for pid in pids.values())
                                             for dataset, pids in report["process_pids"].items()},
                      pid_limit="Datasets without metadata PIDs need separate launch evidence; this analyzer does not establish their process independence.")
    except Exception as exc:
        report["error"] = repr(exc)
        (args.output / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")
        raise
    (args.output / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    with (args.output / "cases.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["dataset", "index", "case", "baseline_us", "candidate_us", "change_percent", "input_sha256"])
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({key: json.dumps(row[key]) if key == "case" else row[key] for key in writer.fieldnames})
    print(json.dumps(dict(summary=report["summary"], datasets=report["datasets"]), indent=2))


if __name__ == "__main__":
    main()
