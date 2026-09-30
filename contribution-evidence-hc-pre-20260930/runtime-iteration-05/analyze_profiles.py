"""Recompute all L1 diagnostics without treating profiler timings as benchmarks."""
import argparse
import collections
import csv
import json
import statistics
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = {"scope": "L1 diagnostics; not benchmark samples", "cases": []}
    fields = ("Duration(us)", "aiv_scalar_time(us)", "aiv_vec_time(us)",
              "aiv_mte3_time(us)", "aicore_time(us)")
    for path in sorted(args.root.glob("div3-profile-*/**/kernel_details.csv")):
        with path.open() as stream:
            rows = [row for row in csv.DictReader(stream) if row["Type"] == "HcPre"]
        if not rows:
            continue
        relative = path.relative_to(args.root)
        trace = json.loads(path.with_name("trace_view.json").read_text())
        events = trace["traceEvents"] if isinstance(trace, dict) else trace
        cpu = [event for event in events
               if event.get("ph") == "X" and event.get("cat") == "cpu_op"]
        names = collections.Counter(event["name"] for event in cpu)
        row = {"experiment": relative.parts[0], "case": relative.parts[2],
               "source": str(relative), "count": len(rows),
               "output_shapes": sorted({item["Output Shapes"] for item in rows}),
               "allocation_events": {name: names[name]
                                     for name in ("empty_tensor", "aten::empty")},
               "hc_pre_cpu_count": sum(count for name, count in names.items()
                                       if "hc_pre" in name.lower())}
        for field in fields:
            values = [float(item[field]) for item in rows if item.get(field)]
            row[field] = statistics.median(values) if values else None
        result["cases"].append(row)
    assert len(result["cases"]) == 28
    args.output.write_text(json.dumps(result, indent=2))
    print("Wrote all", len(result["cases"]), "profiles")


if __name__ == "__main__":
    main()
