"""Frozen actual-indexer NoPE component baseline, never a model benchmark."""

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace

import paired
import test_helper as test
import torch
import torch_npu
import vllm_ascend
from experiment import guard
from torch_npu.profiler.experimental_config import AiCMetrics, ProfilerLevel, _ExperimentalConfig

from production_caller import sparse_mla


def ordered_nope(source, order):
    inputs = dict(source)
    inputs["query_rope"] = None
    inputs["key_rope"] = None
    if order == "chronological":
        indices = source["sparse_indices"].clone()
        for row in indices[:, 0]:
            valid = row[row >= 0].sort().values
            row.fill_(-1)
            row[: len(valid)] = valid
        inputs["sparse_indices"] = indices
    return inputs


def golden(inputs):
    query = inputs["query"].double()
    table = inputs["block_table"].long()[0]
    key = inputs["key"][table, :, 0].reshape(-1, 512).double()
    indices = inputs["sparse_indices"][:, 0].long()
    kv_length = int(inputs["actual_seq_lengths_kv"][0])
    output = torch.zeros_like(query)
    lse = torch.full(query.shape[:2], -torch.inf, dtype=torch.float64)
    for row in range(len(query)):
        visible = kv_length - len(query) + row + 1
        selected = indices[row][(indices[row] >= 0) & (indices[row] < visible)]
        if len(selected):
            scores = (query[row] @ key[selected].T) / math.sqrt(512)
            output[row] = scores.softmax(-1) @ key[selected]
            lse[row] = scores.logsumexp(-1)
    return output, lse


def make_runner(inputs, return_lse):
    if return_lse:

        def run(_):
            return torch.ops._C_ascend.npu_sparse_flash_attention(
                **inputs,
                scale_value=1 / math.sqrt(512),
                sparse_block_size=1,
                layout_query="TND",
                layout_kv="PA_BSND",
                sparse_mode=3,
                attention_mode=2,
                return_softmax_lse=True,
            )

        return run
    query_count = inputs["query"].shape[0]
    prefix = torch.tensor([0, query_count], dtype=torch.int32).npu()
    metadata = SimpleNamespace(
        block_size=128,
        smla_metadata=None,
        block_table=inputs["block_table"],
        query_start_loc=prefix,
        seq_lens=inputs["actual_seq_lengths_kv"],
    )

    def run(_):
        return (sparse_mla(inputs["query"], inputs["key"], inputs["sparse_indices"], metadata, 1 / math.sqrt(512)),)

    return run


def profile_call(run, inputs, trace):
    assert not trace.exists()
    with torch_npu.profiler.profile(
        activities=[torch_npu.profiler.ProfilerActivity.CPU, torch_npu.profiler.ProfilerActivity.NPU],
        schedule=torch_npu.profiler.schedule(wait=0, warmup=5, active=5, repeat=1),
        experimental_config=_ExperimentalConfig(
            profiler_level=ProfilerLevel.Level1, aic_metrics=AiCMetrics.PipeUtilization
        ),
        on_trace_ready=torch_npu.profiler.tensorboard_trace_handler(str(trace)),
    ) as prof:
        for _ in range(10):
            guard()
            run(inputs)
            prof.step()
    guard()
    files = sorted(trace.glob("*_ascend_pt/ASCEND_PROFILER_OUTPUT/kernel_details.csv"))
    assert len(files) == 1, files
    with files[0].open(encoding="utf-8-sig", newline="") as handle:
        return dict(csv=str(files[0]), kernel_rows=list(csv.DictReader(handle)))


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trace-root", type=Path)
    parser.add_argument("--phase", choices=["capture", "check", "measure", "profile"], required=True)
    parser.add_argument("--variant", choices=["baseline", "candidate"], required=True)
    parser.add_argument("--query-counts", type=int, nargs="+", default=[1, 32])
    args = parser.parse_args()
    assert not args.output.exists()
    args.reference.mkdir(parents=True, exist_ok=True)
    if args.phase == "profile":
        assert args.trace_root and not args.trace_root.exists()
        args.trace_root.mkdir(parents=True)
    assert test.enable_custom_op()
    metadata = dict(
        pid=os.getpid(),
        phase=args.phase,
        variant=args.variant,
        device=torch.npu.get_device_name(0),
        package_path=str(Path(vllm_ascend.__file__).parent),
        torch_version=str(torch.__version__),
        torch_npu_version=str(torch_npu.__version__),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        paired_sha256=hashlib.sha256(Path(paired.__file__).read_bytes()).hexdigest(),
        caller_provenance=json.loads(Path(__file__).with_name("caller-provenance.json").read_text()),
    )
    rows = []
    for kind in ["native", "quant"]:
        for dtype in ["torch.float16", "torch.bfloat16"]:
            for query_count in args.query_counts:
                label = f"{kind}-{dtype}-{query_count}"
                path = args.captures / f"{label}-inputs.pt"
                guard()
                source = torch.load(path, weights_only=True)
                for order in ["indexer", "chronological"]:
                    cpu = ordered_nope(source, order)
                    expected, expected_lse = golden(cpu)
                    inputs = {k: v.npu() if isinstance(v, torch.Tensor) else v for k, v in cpu.items()}
                    digest = paired.digest_inputs(cpu)
                    for return_lse in [False, True]:
                        row = dict(
                            case=label,
                            order=order,
                            return_lse=return_lse,
                            input_sha256=digest,
                            capture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                        )
                        guard()
                        try:
                            run = make_runner(inputs, return_lse)
                            result = run(inputs)
                            actual = [x.cpu() for x in result]
                            torch.testing.assert_close(actual[0].double(), expected, rtol=0.01, atol=0.03)
                            if return_lse:
                                assert actual[1].shape == actual[2].shape == (1, *expected_lse.shape)
                                lse = (actual[1].double() + actual[2].double().log()).squeeze(0)
                                torch.testing.assert_close(lse, expected_lse, rtol=0.001, atol=0.005)
                            else:
                                direct = torch.ops._C_ascend.npu_sparse_flash_attention(
                                    **inputs,
                                    scale_value=1 / math.sqrt(512),
                                    sparse_block_size=1,
                                    layout_query="TND",
                                    layout_kv="PA_BSND",
                                    sparse_mode=3,
                                    attention_mode=2,
                                    return_softmax_lse=False,
                                )[0].cpu()
                                assert torch.equal(actual[0].view(torch.uint8), direct.view(torch.uint8))
                            ref = args.reference / f"{label}-{order}-{return_lse}.pt"
                            if args.phase == "capture":
                                assert not ref.exists()
                                torch.save(dict(input_sha256=digest, outputs=actual), ref)
                            else:
                                previous = torch.load(ref, weights_only=True)
                                assert previous["input_sha256"] == digest
                                assert all(
                                    torch.equal(x.contiguous().view(torch.uint8), y.contiguous().view(torch.uint8))
                                    for x, y in zip(actual, previous["outputs"], strict=True)
                                )
                            row.update(
                                status="passed",
                                numerical_reference=True,
                                production_dispatcher_byte_parity=not return_lse,
                            )
                            if args.phase == "measure":
                                test._run = run
                                row["graph_device_us"], row["eager_batch_wall_us"] = paired.measure(inputs)
                            elif args.phase == "profile":
                                trace = args.trace_root / f"{label}-{order}-{return_lse}"
                                row["profile"] = profile_call(run, inputs, trace)
                        except Exception as exc:
                            row.update(status="failed", error=repr(exc))
                        rows.append(row)
                        args.output.write_text(
                            json.dumps(dict(metadata=metadata, complete=False, rows=rows), indent=2) + "\n"
                        )
                        print(json.dumps({k: v for k, v in row.items() if k != "profile"}), flush=True)
    guard()
    passed = len(rows) == 16 * len(args.query_counts) and all(r["status"] == "passed" for r in rows)
    args.output.write_text(
        json.dumps(dict(metadata=metadata, complete=True, all_passed=passed, rows=rows), indent=2) + "\n"
    )
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
