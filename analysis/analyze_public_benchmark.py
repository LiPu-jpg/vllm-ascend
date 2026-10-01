"""Preserve all public benchmark cases, raw timings and three-way memory."""

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path

from analyze_acceptance_matrix import summarize


COUNTS = (1, 2, 4, 8, 16, 20, 21, 24, 25, 32)
CASES = {f"{kind}-torch.{dtype}-{count}" for kind in ("native", "quant")
         for dtype in ("float16", "bfloat16") for count in COUNTS}


def load(path):
    return json.loads(path.read_text())


def read_run(directory, label, phase, lse=False):
    r = load(directory / (label + ".json"))
    assert r["complete"] and r["all_passed"] and r["phase"] == phase and r["return_lse"] == lse
    assert len(r["rows"]) == 40 and {row["case"] for row in r["rows"]} == CASES
    assert all(row["status"] == "passed" for row in r["rows"])
    return r


def compare(runs, capture):
    indexed = {label: {r["case"]: r for r in run["rows"]} for label, run in runs.items()}
    rows = []
    for case in sorted(CASES):
        source = {label: records[case] for label, records in indexed.items()}
        assert all(r["capture_sha256"] == capture[case] for r in source.values()), case
        samples = {label: r["graph_device_us"] for label, r in source.items()}
        assert all(len(v) == 5 and all(math.isfinite(x) and x > 0 for x in v) for v in samples.values())
        medians = {label: statistics.median(values) for label, values in samples.items()}
        b = statistics.median(samples["b1"] + samples["b2"])
        c = statistics.median(samples["c1"] + samples["c2"])
        rows.append(dict(case=case, query_count=int(case.rsplit("-", 1)[1]),
                         capture_sha256=capture[case], baseline_us=b, candidate_us=c,
                         change_percent=(c / b - 1) * 100, raw_device_us=samples,
                         process_medians_us=medians,
                         separated_lower=max(medians["c1"], medians["c2"]) < min(medians["b1"], medians["b2"]),
                         separated_higher=min(medians["c1"], medians["c2"]) > max(medians["b1"], medians["b2"])))
    return dict(rows=rows, summary=summarize(rows),
                by_query_count={str(count): summarize([r for r in rows if r["query_count"] == count]) for count in COUNTS})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forward", type=Path, required=True)
    parser.add_argument("--reverse", type=Path)
    parser.add_argument("--known-hosts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert (args.forward / "controller.exit").read_text().strip() == "0"
    capture_run = read_run(args.forward, "capture", "capture")
    capture = {row["case"]: row["capture_sha256"] for row in capture_run["rows"]}
    known = load(args.known_hosts)
    assert known["complete"]
    hashes = {variant: next(r["sha256"] for r in known["loaded_host_records"] if r["label"] == "smoke-" + variant)
              for variant in ("control", "candidate")}
    hashes["launch_only"] = next(r["sha256"] for r in known["loaded_host_records"] if r["label"] == "memory-launch_only")
    inspected = []

    def check_run(directory, label, variant):
        successes = [f for f in directory.glob(label + "-attempt-*.exit") if f.read_text().strip() == "0"]
        assert len(successes) == 1, (directory, label)
        path = successes[0].with_name(successes[0].stem + "-maps.json")
        r = load(path)
        host = r["expected_host_tiling"]
        runtime = {"control": "runtime_control_e1_v4", "candidate": "runtime_candidate_e2", "launch_only": "runtime_candidate_e1_v4"}[variant]
        assert "/" + runtime + "/" in host
        assert host.endswith("/lib/linux/aarch64/libcust_opmaster_rt2.0.so")
        assert r["status"] == 0 and r["expected_host_tiling_loaded"] and r["loaded_libraries"][host] == hashes[variant]
        custom = [f for f in r["loaded_libraries"] if "/vendors/custom_transformer/" in f
                  and (f.endswith("/liboptiling.so") or f.endswith("/libcust_opmaster_rt2.0.so"))]
        assert custom == [host]
        inspected.append(dict(directory=directory.name, label=label, variant=variant, sha256=hashes[variant]))
        return successes[0].stem

    forward = {label: read_run(args.forward, "measure-" + label, "measure") for label in ("b1", "c1", "c2", "b2")}
    for label in forward:
        check_run(args.forward, "measure-" + label, "control" if label.startswith("b") else "candidate")
    memory = {variant: read_run(args.forward, "memory-" + variant, "memory") for variant in ("control", "launch_only", "candidate")}
    for variant in memory:
        check_run(args.forward, "memory-" + variant, variant)
    lse = {variant: read_run(args.forward, "lse-" + variant, "measure", True) for variant in ("control", "candidate")}
    for variant in lse:
        check_run(args.forward, "lse-" + variant, variant)
    all_runs = [capture_run, *forward.values(), *memory.values(), *lse.values()]
    reverse = None
    reverse_pids = {}
    if args.reverse is not None:
        assert (args.reverse / "controller.exit").read_text().strip() == "0"
        reverse = {label: read_run(args.reverse, label, "measure") for label in ("c1", "b1", "b2", "c2")}
        for label in reverse:
            attempt = check_run(args.reverse, label, "control" if label.startswith("b") else "candidate")
            reverse_pids[label] = int((args.reverse / (attempt + ".pid")).read_text())
        assert len(set(reverse_pids.values())) == 4
        all_runs.extend(reverse.values())
    for run in all_runs:
        for key in ("device", "torch_version", "torch_npu_version", "script_sha256", "samples", "replays", "graph_calls"):
            assert run[key] == capture_run[key], key
        assert {row["case"]: row["capture_sha256"] for row in run["rows"]} == capture
    assert capture_run["samples"] == 5 and capture_run["replays"] == 100 and capture_run["graph_calls"] == 8
    memory_indexed = {variant: {r["case"]: r for r in run["rows"]} for variant, run in memory.items()}
    memory_rows = []
    for case in sorted(CASES):
        observations = {variant: records[case]["allocator_observations"] for variant, records in memory_indexed.items()}
        reductions = {mode: observations["control"][mode]["peak_increase_bytes"] - observations["candidate"][mode]["peak_increase_bytes"] for mode in ("eager", "graph")}
        memory_rows.append(dict(case=case, query_count=int(case.rsplit("-", 1)[1]), capture_sha256=capture[case],
                                observations=observations, original_to_candidate_reduction_bytes=reductions))
    report = dict(complete=True, forward_order="B/C/C/B", forward=compare(forward, capture),
                  reverse_order="C/B/B/C" if reverse else None, reverse=compare(reverse, capture) if reverse else None,
                  reverse_process_pids=reverse_pids, memory_rows=memory_rows, lse_diagnostic_cases_per_build=40,
                  loaded_host_records=inspected, public_script_sha256=capture_run["script_sha256"],
                  scope="All40 public cases and raw samples retained. Torch allocator observations and SFA device latency only; no whole-model claim.")
    report["artifact_sha256"] = {"forward/" + f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                                 for f in args.forward.glob("*.json")}
    if args.reverse:
        report["artifact_sha256"].update({"reverse/" + f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                                          for f in args.reverse.glob("*.json")})
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"forward": report["forward"]["summary"],
                      "reverse": report["reverse"]["summary"] if reverse else None}, indent=2))


if __name__ == "__main__":
    main()
