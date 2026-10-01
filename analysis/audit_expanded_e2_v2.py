"""Verify the final public suite, all expanded cases and canonical E2 hosts."""

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def load(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    root = args.root
    scripts = root / "active-workspace-20261001"
    results = root / "iteration-e2/acceptance-v1"
    controls = root / "reference-controls-20261001"
    assert (results / "controller.exit").read_text().strip() == "0"
    assert (controls / "controller.exit").read_text().strip() == "0"
    for name, expected in load(scripts / "acceptance-e2-harness-sha256.json").items():
        assert hashlib.sha256((scripts / name).read_bytes()).hexdigest() == expected, name
    source = load(scripts / "manifest-e2.json")
    for name, expected in source["source_hashes"].items():
        assert hashlib.sha256((root / "candidate-e2/csrc" / name).read_bytes()).hexdigest() == expected, name
    provenance = load(root / "iteration-e2/installed-provenance.json")
    assert provenance["identical_original_kernel_binaries"] and len(provenance["changed_runtime_files"]) == 1
    hosts = {
        "control": (root / "runtime_control_e1_v4", provenance["original_host_sha256"]),
        "candidate": (root / "runtime_candidate_e2", provenance["host_sha256"]),
    }
    relative = Path("vllm_ascend/_cann_ops_custom/vendors/custom_transformer/op_impl/ai_core/tbe/op_tiling/lib/linux/aarch64/libcust_opmaster_rt2.0.so")
    for runtime, expected in hosts.values():
        assert hashlib.sha256((runtime / relative).read_bytes()).hexdigest() == expected
    labels = {"full-tests-control": "control", "full-tests-candidate": "candidate"}
    labels.update({f"{name}-candidate": "candidate" for name in ("correctness", "coverage", "dcp", "edges")})
    labels.update({"large-bounds-control": "control", "large-bounds-candidate": "candidate",
                   "boundary-capture": "control", "boundary-check": "candidate"})
    for dataset in ("boundary", "paired", "unsorted", "indexer", "page48"):
        labels.update({f"{dataset}-{suffix}": "control" if suffix.startswith("b") else "candidate"
                       for suffix in ("b1", "c1", "c2", "b2")})
    mappings = []
    successful_attempts = {}
    for label, variant in labels.items():
        successes = [f for f in results.glob(f"{label}-attempt-*.exit") if f.read_text().strip() == "0"]
        assert len(successes) == 1, (label, successes)
        success = successes[0]
        successful_attempts[label] = success.stem
        record = load(success.with_name(success.stem + "-maps.json"))
        runtime, expected = hosts[variant]
        host = str(runtime / relative)
        assert record["status"] == 0 and record["expected_host_tiling_loaded"]
        assert record["expected_host_tiling"] == host and record["loaded_libraries"][host] == expected
        custom = [f for f in record["loaded_libraries"] if "/vendors/custom_transformer/" in f
                  and (f.endswith("/liboptiling.so") or f.endswith("/libcust_opmaster_rt2.0.so"))]
        assert custom == [host], (label, custom)
        mappings.append(dict(label=label, variant=variant, sha256=expected))
    for variant in ("control", "candidate"):
        label = "full-tests-" + variant
        r = load(results / (label + ".json"))
        assert r["complete"] and r["cases"] == 616 and r["failures"] == r["skipped"] == r["exit_code"] == 0
        cases = list(ET.parse(results / (successful_attempts[label] + ".xml")).getroot().iter("testcase"))
        assert len(cases) == 616
        assert all(not any(c.tag in ("failure", "error", "skipped") for c in case) for case in cases)
        counts = {}
        for case in cases:
            name = case.attrib["classname"].rsplit(".", 1)[-1]
            counts[name] = counts.get(name, 0) + 1
        assert counts == {"test_sparse_flash_attention_active_cores": 402,
                          "test_sparse_flash_attention_active_workspace": 16,
                          "test_sparse_flash_attention_sparse_indices": 198}, counts
    expected_counts = {"correctness": 60, "coverage": 98, "dcp": 80, "edges": 78}
    known_reference_failures = {}
    for name, count in expected_counts.items():
        r = load(results / f"{name}-candidate.json")
        assert r["complete"] and len(r["rows"]) == count
        original = None
        if name in ("coverage", "edges"):
            label = name + "-control-replay"
            original = load(controls / (label + ".json"))
            assert original["complete"] and len(original["rows"]) == count
            successes = [f for f in controls.glob(label + "-attempt-*.exit") if f.read_text().strip() == "0"]
            assert len(successes) == 1
            mapping = load(successes[0].with_name(successes[0].stem + "-maps.json"))
            host = str(hosts["control"][0] / relative)
            assert mapping["status"] == 0 and mapping["expected_host_tiling_loaded"]
            assert mapping["expected_host_tiling"] == host and mapping["loaded_libraries"][host] == hosts["control"][1]
        failures = []
        for index, row in enumerate(r["rows"]):
            reference_failure = row.get("nonempty_reference") == "failed" or row.get("reference_passed") is False
            if original is not None:
                before = original["rows"][index]
                for key in ("index", "dtype", "rope_dim", "layout", "sparse_block_size", "sparse_mode", "heads", "selected_tokens", "kind", "capacity", "block", "mode", "input_sha256"):
                    assert before.get(key) == row.get(key), (name, index, key)
                for key in ("nonempty_reference", "reference_passed", "reference_error"):
                    assert before.get(key) == row.get(key), (name, index, key)
                if "bytewise_baseline_by_output" in before:
                    assert all(before["bytewise_baseline_by_output"])
                if "bytewise_parity" in before:
                    assert before["bytewise_parity"] == "passed"
            if reference_failure:
                assert original is not None
                if name == "coverage":
                    assert row["layout"] == "BSND" and row["sparse_block_size"] == 8
                else:
                    assert row["block"] in (2, 4)
                failures.append(row)
            for key in ("nonempty_correctness", "nonempty_reference", "reference", "bytewise_parity"):
                if key in row:
                    assert row[key] == "passed" or (key == "nonempty_reference" and reference_failure), (name, key, row)
            for key in ("bitwise_baseline", "remap_exact", "reference_passed"):
                if key in row:
                    assert row[key] is True or (key == "reference_passed" and reference_failure), (name, key, row)
            if "bytewise_baseline_by_output" in row:
                assert all(row["bytewise_baseline_by_output"])
            assert row.get("reference_error") is None or reference_failure, (name, row)
        if original is not None:
            assert len(failures) == {"coverage": 8, "edges": 20}[name]
            known_reference_failures[name] = failures
    bounds = [load(results / f"large-bounds-{variant}.json") for variant in ("control", "candidate")]
    assert all(r["complete"] and len(r["rows"]) == 10 for r in bounds)
    for baseline, candidate in zip(bounds[0]["rows"], bounds[1]["rows"]):
        assert baseline["input_sha256"] == candidate["input_sha256"]
        assert baseline["reference_passed"] and candidate["reference_passed"]
        assert candidate["status"] == "byte_parity_passed"
    capture = load(results / "indexer-boundaries.json")
    assert capture["complete"] and capture["all_passed"] and len(capture["rows"]) == 48
    boundary = load(results / "boundary-analysis.json")
    assert boundary["complete"] and len(boundary["rows"]) == 192
    for label in ("boundary-capture", "boundary-check"):
        r = load(results / (label + ".json"))
        assert r["complete"] and r["all_passed"] and len(r["rows"]) == 192
        assert all(row["numerical_reference"] and row["production_dispatcher_byte_parity"] for row in r["rows"])
    matrix = load(args.matrix)
    assert matrix["complete"] and len(matrix["rows"]) == 172
    for name, expected in matrix["input_files_sha256"].items():
        assert hashlib.sha256((results / name).read_bytes()).hexdigest() == expected
    report = dict(complete=True, source_commit=source["commit"], total_pytest_cases_per_build=616,
                  public_tests_per_build=418, retained_private_tests_per_build=198,
                  retained_checks=expected_counts, large_index_cases_per_build=10,
                  boundary_performance_cases=192, retained_performance_cases=172,
                  existing_reference_failures=known_reference_failures,
                  loaded_host_records=mappings, kernel_binaries_unchanged=True,
                  scope="One physical A2; all samples, slowdowns and existing oracle failures retained. The 8 BSND/block8 and 20 partial-block oracle failures are byte-identical to frozen references and freshly reproduced on the original control; they are not numerical passes. Public benchmark and reverse confirmation are audited separately. A3, distributed and whole-model behavior remain unverified.")
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("public_tests_per_build", "retained_private_tests_per_build", "boundary_performance_cases", "retained_performance_cases")}, indent=2))


if __name__ == "__main__":
    main()
