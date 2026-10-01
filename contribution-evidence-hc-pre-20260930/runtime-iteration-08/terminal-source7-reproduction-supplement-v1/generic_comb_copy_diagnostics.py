"""Check generic comb layout widths with the real production plugin.

All failures are retained. This is correctness coverage, not a benchmark.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import torch
import torch.nn.functional as F
import torch_npu
from vllm_ascend.utils import enable_custom_op


def hf32(values):
    bits = values.contiguous().view(torch.int32)
    return ((bits + (1 << 11)) & ~((1 << 12) - 1)).view(torch.float32)


def reference(x, fn, scale, base, width, iters):
    flat = x.float().flatten(-2)
    inverse = torch.rsqrt(flat.square().mean(-1, keepdim=True) + 1e-6)
    mixed = F.linear(hf32(flat), hf32(fn)) * inverse
    pre, post, comb = mixed.split([width, width, width * width], dim=-1)
    pre = torch.sigmoid(pre * scale[0] + base[:width]) + 1e-6
    post = 2 * torch.sigmoid(post * scale[1] + base[width : 2 * width])
    comb = (comb * scale[2] + base[2 * width :]).unflatten(-1, (width, width))
    comb = comb.softmax(-1) + 1e-6
    comb = comb / (comb.sum(-2, keepdim=True) + 1e-6)
    for _ in range(iters - 1):
        comb = comb / (comb.sum(-1, keepdim=True) + 1e-6)
        comb = comb / (comb.sum(-2, keepdim=True) + 1e-6)
    y = (pre.unsqueeze(-1) * x.float()).sum(-2).to(x.dtype)
    return y, post, comb, pre


def bits_equal(left, right):
    return torch.equal(
        left.contiguous().view(torch.uint8), right.contiguous().view(torch.uint8)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    assert enable_custom_op()
    torch_npu.npu.config.allow_internal_format = True
    torch.set_num_threads(1)
    rows = []
    with torch.inference_mode():
        for width, tokens, signed, iters in itertools.product(
            (1, 3, 8), (1, 17), (False, True), (1, 3)
        ):
            generator = torch.Generator().manual_seed(1024)
            fan = width * 4096
            mix = width * (width + 2)
            x = (torch.rand(tokens, width, 4096, generator=generator) * 2).bfloat16()
            fn = torch.rand(mix, fan, generator=generator) / fan
            scale = torch.rand(3, generator=generator) * 2
            base = torch.rand(mix, generator=generator) * 2
            if signed:
                x = (x.float() - 1).bfloat16()
                fn = (fn - 0.5 / fan) * fan**0.5
                base = torch.linspace(-3, 3, mix)
            cpu_inputs = (x, fn, scale, base)
            inputs = tuple(value.npu() for value in cpu_inputs)
            expected = reference(*cpu_inputs, width, iters)
            key = f"hc{width}-t{tokens}-signed{int(signed)}-i{iters}"
            row = {
                "case": key,
                "cpu_accuracy_pass": False,
                "errors": [],
                "cpu_metrics": [],
                "input_sha256": [
                    hashlib.sha256(
                        v.contiguous().view(torch.uint8).numpy().tobytes()
                    ).hexdigest()
                    for v in cpu_inputs
                ],
            }

            def call(inputs=inputs, width=width, iters=iters):
                return torch.ops._C_ascend.npu_hc_pre_v3(
                    *inputs,
                    None,
                    hc_mult=width,
                    hc_sinkhorn_iters=iters,
                    norm_eps=1e-6,
                    hc_eps=1e-6,
                )

            try:
                actual = call()
                repeated = call()
                graph = torch.npu.NPUGraph()
                with torch.npu.graph(graph):
                    captured = call()
                graph.replay()
                torch.npu.synchronize()
                cpu = tuple(value.cpu() for value in actual)
                for index, (value, target) in enumerate(
                    zip(cpu, expected, strict=True)
                ):
                    difference = (value.float() - target.float()).abs()
                    threshold, required = (4e-3, 0.98) if index == 0 else (1e-4, 0.995)
                    magnitude = torch.maximum(value.float().abs(), target.float().abs())
                    close = (difference <= threshold) | (
                        difference
                        / magnitude.clamp_min(torch.finfo(torch.float32).tiny)
                        <= threshold
                    )
                    finite = bool(
                        torch.isfinite(value).all() and torch.isfinite(target).all()
                    )
                    metric = {
                        "output": index,
                        "finite": finite,
                        "pass_rate": close.float().mean().item(),
                        "max_abs_diff": difference.max().item(),
                        "threshold": threshold,
                        "required": required,
                    }
                    metric["pass"] = finite and metric["pass_rate"] >= required
                    row["cpu_metrics"].append(metric)
                    for kind, values in (("repeat", repeated), ("graph", captured)):
                        if not bits_equal(actual[index], values[index]):
                            row["errors"].append(f"{kind}:{index}")
                row["cpu_accuracy_pass"] = all(
                    metric["pass"] for metric in row["cpu_metrics"]
                )
                for index, (value, original) in enumerate(
                    zip(inputs, cpu_inputs, strict=True)
                ):
                    if not bits_equal(value.cpu(), original):
                        row["errors"].append(f"input:{index}")
                if args.reference:
                    previous = torch.load(
                        args.reference / f"{key}.pt", weights_only=True
                    )
                    for index, (value, original) in enumerate(
                        zip(cpu_inputs, previous["inputs"], strict=True)
                    ):
                        if not bits_equal(value, original):
                            row["errors"].append(f"baseline-input:{index}")
                    for index, (value, original) in enumerate(
                        zip(expected, previous["expected"], strict=True)
                    ):
                        if not bits_equal(value, original):
                            row["errors"].append(f"baseline-expected:{index}")
                    for index, (value, target) in enumerate(
                        zip(cpu, previous["outputs"], strict=True)
                    ):
                        if not bits_equal(value, target):
                            row["errors"].append(f"baseline:{index}")
                destination = args.output / f"{key}.pt"
                torch.save(
                    {"inputs": cpu_inputs, "expected": expected, "outputs": cpu},
                    destination,
                )
                row["tensor_sha256"] = hashlib.sha256(
                    destination.read_bytes()
                ).hexdigest()
                del graph
            except (
                RuntimeError,
                ValueError,
                TypeError,
                AssertionError,
                OSError,
            ) as error:
                row["errors"].append(f"{type(error).__name__}:{error}")
            rows.append(row)
            (args.output / "results.json").write_text(json.dumps(rows, indent=2) + "\n")
            print(
                "GENERIC_COMB_RESULT",
                key,
                row["cpu_accuracy_pass"],
                row["errors"],
                flush=True,
            )
    assert len(rows) == 24
    print("GENERIC_COMB_ALL_RESULTS_RECORDED", len(rows), flush=True)
    raise SystemExit(any(not row["cpu_accuracy_pass"] or row["errors"] for row in rows))


if __name__ == "__main__":
    main()
