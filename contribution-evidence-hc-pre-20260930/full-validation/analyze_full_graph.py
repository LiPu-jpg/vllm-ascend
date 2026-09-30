import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
DEST = Path(sys.argv[2])
DEST.mkdir(parents=True, exist_ok=True)


def percentile(values, fraction):
    values = sorted(values)
    return values[round((len(values) - 1) * fraction)]


summaries = {}
for timing, prefix in [("graph", "")]:
    arms = {}
    for step in ["baseline-a", "candidate-a", "candidate-b", "baseline-b"]:
        label = prefix + step
        source = ROOT / ("full-operator-v5/graph/results.json" if step == "baseline-a" else f"full-graph-{step}/data/results.json")
        if not source.exists():
            continue
        data = json.loads(source.read_text())
        assert len(data["cases"]) == 28, source
        assert data.get("timing", "event") == timing
        cases = {}
        for case in data["cases"]:
            assert len(case["rounds"]) == 3
            if label != "baseline-a":
                assert case["bitwise_reference_checked"], (label, case["case"])
            values = []
            walls = []
            medians = []
            for record in case["rounds"]:
                assert len(record["event_us"]) == 70
                assert len(record["wall_us"]) == 70
                assert all(v > 0 for v in record["event_us"] + record["wall_us"])
                values.extend(record["event_us"][data["warmup"]:])
                walls.extend(record["wall_us"][data["warmup"]:])
                medians.append(record["event_median_us"])
            cases[case["case"]] = (values, walls, medians)
        arms[step] = cases
    if len(arms) != 4:
        continue
    assert all(set(arm) == set(arms["baseline-a"]) for arm in arms.values())
    rows = []
    for key in arms["baseline-a"]:
        base_values = arms["baseline-a"][key][0] + arms["baseline-b"][key][0]
        candidate_values = arms["candidate-a"][key][0] + arms["candidate-b"][key][0]
        base = statistics.median(base_values)
        candidate = statistics.median(candidate_values)
        rows.append(dict(
            case=key,
            baseline_median_us=base,
            candidate_median_us=candidate,
            baseline_p10_us=percentile(base_values, .1),
            baseline_p90_us=percentile(base_values, .9),
            candidate_p10_us=percentile(candidate_values, .1),
            candidate_p90_us=percentile(candidate_values, .9),
            latency_change_percent=100 * (candidate / base - 1),
            speedup=base / candidate,
            baseline_round_medians=arms["baseline-a"][key][2] + arms["baseline-b"][key][2],
            candidate_round_medians=arms["candidate-a"][key][2] + arms["candidate-b"][key][2],
            baseline_wall_median_us=statistics.median(arms["baseline-a"][key][1] + arms["baseline-b"][key][1]),
            candidate_wall_median_us=statistics.median(arms["candidate-a"][key][1] + arms["candidate-b"][key][1]),
        ))
    summaries[timing] = dict(
        scope="Full HcPre operator, ABBA, both complete repetitions pooled; no model claim",
        cases=rows,
        faster=sum(r["latency_change_percent"] < 0 for r in rows),
        slower=sum(r["latency_change_percent"] > 0 for r in rows),
        geomean_speedup=math.exp(statistics.mean(math.log(r["speedup"]) for r in rows)),
    )
(DEST / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
lines = ["# Full-plugin HcPre graph comparison", "", "All cases and six round medians per arm remain in summary.json and raw results.", ""]
for timing, summary in summaries.items():
    lines += [f"## {timing}", "",
              f"Faster: {summary['faster']}/28; slower: {summary['slower']}/28; geometric mean speedup: {summary['geomean_speedup']:.5f}.", "",
              "| Case | Baseline median [p10, p90] us | Candidate median [p10, p90] us | Latency change |",
              "| --- | ---: | ---: | ---: |"]
    for row in summary["cases"]:
        lines.append(f"| {row['case']} | {row['baseline_median_us']:.3f} [{row['baseline_p10_us']:.3f}, {row['baseline_p90_us']:.3f}] | {row['candidate_median_us']:.3f} [{row['candidate_p10_us']:.3f}, {row['candidate_p90_us']:.3f}] | {row['latency_change_percent']:+.2f}% |")
    lines.append("")
(DEST / "comparison.md").write_text("\n".join(lines) + "\n")
print({timing: {key: value for key, value in summary.items() if key != "cases"} for timing, summary in summaries.items()})
