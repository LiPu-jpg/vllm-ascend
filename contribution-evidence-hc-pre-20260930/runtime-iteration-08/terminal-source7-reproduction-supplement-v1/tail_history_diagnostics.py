"""Use valid preceding calls to test whether fixed HcPre inputs depend on history."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op


def digest(tensor):
    return hashlib.sha256(
        tensor.contiguous().view(torch.uint8).numpy().tobytes()
    ).hexdigest()


def equal_bytes(left, right):
    return torch.equal(
        left.contiguous().view(torch.uint8), right.contiguous().view(torch.uint8)
    )


def metrics(actual, expected):
    rows = []
    for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
        diff = (left.float() - right.float()).abs()
        rows.append(
            {
                "output": index,
                "byte_equal": equal_bytes(left, right),
                "max_abs_difference": float(diff.max()),
                "different_values": int((left != right).sum()),
                "nonfinite_count": int((~torch.isfinite(left)).sum()),
            }
        )
    return rows


def call(inputs, iters, pre_mix=None):
    return torch.ops._C_ascend.npu_hc_pre_v3(
        *inputs, pre_mix, hc_mult=4, hc_sinkhorn_iters=iters, norm_eps=1e-6, hc_eps=1e-6
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    assert enable_custom_op()
    torch_npu.npu.config.allow_internal_format = True
    torch.set_num_threads(1)
    spec = importlib.util.spec_from_file_location("hf32_oracle", args.oracle)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    all_rows = []
    iters = 20
    with torch.inference_mode():
        for hidden in (4103, 4104, 7168, 7169):
            for tokens in (1, 17):
                for signed in (False, True):
                    target = f"t{tokens}-d{hidden}-signed{int(signed)}"
                    x, fn, scale, base = oracle._make_hc_pre_inputs((tokens, 4, hidden))
                    if signed:
                        x = (x.float() - 1).bfloat16()
                        fn = fn - 0.5 / (4 * hidden)
                        base = torch.linspace(-3, 3, 24)
                    cpu_inputs = (x, fn, scale, base)
                    input_hashes = [digest(t) for t in cpu_inputs]
                    inputs = tuple(t.npu() for t in cpu_inputs)
                    originals = tuple(t.clone() for t in inputs)
                    expected = oracle._hc_pre_cpu(*cpu_inputs, sinkhorn_iters=iters)
                    pre_mix_cpu = torch.ones(tokens, 4)
                    pre_mix = pre_mix_cpu.npu()
                    expected_external = oracle._hc_pre_cpu(
                        *cpu_inputs, pre_mix=pre_mix_cpu, sinkhorn_iters=iters
                    )
                    first = None
                    # 8192 uses full K chunks on every Cube core, including the
                    # extra core holding the four-element 7169 tail.
                    for preceding_hidden, amplitude in (
                        (hidden, 0),
                        (hidden, 16),
                        (8192, 0),
                        (8192, 16),
                    ):
                        key = f"{target}-previousd{preceding_hidden}-a{amplitude}"
                        row = {
                            "case": key,
                            "target": target,
                            "input_sha256": input_hashes,
                            "previous_hidden": preceding_hidden,
                            "previous_amplitude": amplitude,
                            "cpu_accuracy_pass": False,
                            "cpu_errors": [],
                            "errors": [],
                        }
                        try:
                            prior_cpu = (
                                torch.full(
                                    (tokens, 4, preceding_hidden),
                                    float(amplitude),
                                    dtype=torch.bfloat16,
                                ),
                                torch.full(
                                    (24, 4 * preceding_hidden),
                                    float(amplitude) / (4 * preceding_hidden),
                                ),
                                torch.ones(3),
                                torch.zeros(24),
                            )
                            prior = tuple(t.npu() for t in prior_cpu)
                            prior_outputs = call(prior, iters)
                            torch.npu.synchronize()
                            row["previous_outputs_finite"] = all(
                                bool(torch.isfinite(t).all()) for t in prior_outputs
                            )
                            actual = call(inputs, iters)
                            repeated = call(inputs, iters)
                            external = call(inputs, iters, pre_mix)
                            graph = torch.npu.NPUGraph()
                            with torch.npu.graph(graph):
                                captured = call(inputs, iters)
                            call(prior, iters)
                            graph.replay()
                            torch.npu.synchronize()
                            saved = {
                                "actual": tuple(t.cpu() for t in actual),
                                "repeat": tuple(t.cpu() for t in repeated),
                                "external_pre_mix": tuple(t.cpu() for t in external),
                                "graph_after_previous_call": tuple(
                                    t.cpu() for t in captured
                                ),
                                "expected": expected,
                                "expected_external_pre_mix": expected_external,
                            }
                            if first is None:
                                first = saved["actual"]
                            row["history_comparison"] = metrics(saved["actual"], first)
                            row["repeat_comparison"] = metrics(
                                saved["repeat"], saved["actual"]
                            )
                            row["graph_comparison"] = metrics(
                                saved["graph_after_previous_call"], saved["actual"]
                            )
                            for kind, wanted in (
                                ("actual", expected),
                                ("external_pre_mix", expected_external),
                                ("graph_after_previous_call", expected),
                            ):
                                for index, (value, golden) in enumerate(
                                    zip(saved[kind], wanted, strict=True)
                                ):
                                    try:
                                        assert bool(torch.isfinite(value).all())
                                        oracle._assert_close_with_pass_rate(
                                            value,
                                            golden,
                                            diff_threshold=oracle.Y_DIFF_THRESHOLD
                                            if index == 0
                                            else oracle.AUX_DIFF_THRESHOLD,
                                            required_pass_rate=oracle.Y_REQUIRED_PASS_RATE
                                            if index == 0
                                            else oracle.AUX_REQUIRED_PASS_RATE,
                                        )
                                    except AssertionError as error:
                                        row["cpu_errors"].append(
                                            f"{kind}:{index}:{error}"
                                        )
                            row["cpu_accuracy_pass"] = not row["cpu_errors"]
                            for value, original in zip(inputs, originals, strict=True):
                                if not equal_bytes(value, original):
                                    row["errors"].append("target input changed")
                            path = args.output / f"{key}.pt"
                            torch.save(saved, path)
                            row["saved_sha256"] = hashlib.sha256(
                                path.read_bytes()
                            ).hexdigest()
                            del (
                                graph,
                                prior_outputs,
                                prior,
                                actual,
                                repeated,
                                external,
                                captured,
                            )
                        except (
                            AssertionError,
                            RuntimeError,
                            TypeError,
                            ValueError,
                            OSError,
                        ) as error:
                            row["errors"].append(f"{type(error).__name__}:{error}")
                        all_rows.append(row)
                        (args.output / "results.json").write_text(
                            json.dumps(all_rows, indent=2) + "\n"
                        )
                        print(key, json.dumps(row), flush=True)
    assert len(all_rows) == 64
    failed = any(
        not row["cpu_accuracy_pass"]
        or row["errors"]
        or any(
            not metric["byte_equal"]
            for name in ("history_comparison", "repeat_comparison", "graph_comparison")
            for metric in row.get(name, [])
        )
        for row in all_rows
    )
    print("ALL64_HISTORY_DIAGNOSTIC_RESULTS_RECORDED;_FAILURES_RETAINED", flush=True)
    raise SystemExit(int(failed))


if __name__ == "__main__":
    main()
