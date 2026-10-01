"""Audit actual host execution, unchanged kernels, tests and every E2 comparison."""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    results = args.root / "iteration-e2"
    screen = results / "screen-v1"
    allocation = results / "allocation-only"
    assert (results / "candidate-build.exit").read_text().strip() == "0"
    assert (results / "build-controller.exit").read_text().strip() == "0"
    assert (screen / "screen-controller.exit").read_text().strip() == "0"
    manifest = json.loads(
        (args.root / "active-workspace-20261001/manifest-e2.json").read_text()
    )
    for name, expected in manifest["source_hashes"].items():
        assert digest(args.root / "candidate-e2/csrc" / name) == expected, name
    provenance = json.loads((results / "installed-provenance.json").read_text())
    assert provenance["identical_original_kernel_binaries"]
    assert len(provenance["changed_runtime_files"]) == 1
    e1 = json.loads(
        (args.root / "iteration-e1/installed-provenance-v4.json").read_text()
    )
    hashes = dict(
        control=provenance["original_host_sha256"],
        candidate=provenance["host_sha256"],
        launch_only=e1["packages"]["candidate"]["host_sha256"],
    )
    runtimes = dict(
        control=args.root / "runtime_control_e1_v4",
        candidate=args.root / "runtime_candidate_e2",
        launch_only=args.root / "runtime_candidate_e1_v4",
    )
    relative = Path(
        "vllm_ascend/_cann_ops_custom/vendors/custom_transformer/op_impl/ai_core/tbe/op_tiling/lib/linux/aarch64/libcust_opmaster_rt2.0.so"
    )
    mapping_records = []
    for directory, labels in [
        (
            screen,
            dict(
                [
                    ("smoke-control", "control"),
                    ("smoke-candidate", "candidate"),
                    ("pytest-control", "control"),
                    ("pytest-candidate", "candidate"),
                    ("nope-capture", "control"),
                    ("nope-check", "candidate"),
                    ("nope-b1", "control"),
                    ("nope-c1", "candidate"),
                    ("nope-c2", "candidate"),
                    ("nope-b2", "control"),
                    ("profile-control", "control"),
                    ("profile-candidate", "candidate"),
                    ("memory-control", "control"),
                    ("memory-launch_only", "launch_only"),
                    ("memory-candidate", "candidate"),
                ]
            ),
        ),
        (
            allocation,
            dict(
                [
                    ("nope-capture", "launch_only"),
                    ("nope-check", "candidate"),
                    ("nope-b1", "launch_only"),
                    ("nope-c1", "candidate"),
                    ("nope-c2", "candidate"),
                    ("nope-b2", "launch_only"),
                ]
            ),
        ),
    ]:
        for label, variant in labels.items():
            exits = [
                path
                for path in directory.glob(f"{label}-attempt-*.exit")
                if path.read_text().strip() == "0"
            ]
            assert len(exits) == 1, (label, exits)
            path = exits[0].with_name(exits[0].stem + "-maps.json")
            record = json.loads(path.read_text())
            host = str(runtimes[variant] / relative)
            assert record["status"] == 0 and record["expected_host_tiling_loaded"]
            assert (
                record["expected_host_tiling"] == host
                and record["loaded_libraries"][host] == hashes[variant]
            )
            custom_hosts = [
                name
                for name in record["loaded_libraries"]
                if "/vendors/custom_transformer/" in name
                and (
                    name.endswith("/liboptiling.so")
                    or name.endswith("/libcust_opmaster_rt2.0.so")
                )
            ]
            assert custom_hosts == [host], (label, custom_hosts)
            mapping_records.append(
                dict(
                    directory=directory.name,
                    label=label,
                    variant=variant,
                    sha256=hashes[variant],
                )
            )
    assert len(mapping_records) == 21
    for variant in ["control", "candidate"]:
        tests = json.loads((screen / f"pytest-{variant}.json").read_text())
        assert (
            tests["complete"]
            and tests["cases"] == 520
            and tests["failures"] == tests["skipped"] == tests["exit_code"] == 0
        )
    profiles = json.loads((screen / "actual-launch-gate.json").read_text())
    assert profiles["passed"] and len(profiles["records"]) == 64
    for row in profiles["records"]:
        count = int(row["case"].rsplit("-", 1)[1])
        expected = min(count, 20) if row["variant"] == "candidate" else 20
        assert row["aic"] == expected and row["aiv"] == 2 * expected
    comparisons = {}
    for directory in [screen, allocation]:
        report = json.loads((directory / "nope-screening-analysis.json").read_text())
        assert report["complete"] and len(report["rows"]) == 32
        comparisons[directory.name] = report["groups"]
    memory = json.loads((results / "memory-analysis.json").read_text())
    assert memory["complete"] and len(memory["rows"]) == 32
    for name, expected in provenance["artifacts"].items():
        assert digest(runtimes["candidate"] / name) == expected, name
    record = dict(
        complete=True,
        source_commit=manifest["commit"],
        loaded_host_records=mapping_records,
        tests_per_build=520,
        launch_profiles=64,
        latency_comparisons=comparisons,
        memory_groups=memory["groups"],
        kernel_binaries_unchanged=True,
        scope="Isolated SFA components on one physical A2. All raw cases and regressions retained. Public benchmark, expanded regression, physical A3, distributed and whole-model validation remain pending.",
    )
    args.output.write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: record[key]
                for key in ["tests_per_build", "launch_profiles", "memory_groups"]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
