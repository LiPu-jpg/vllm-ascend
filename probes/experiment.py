"""Initial native comparison; preserve every observation and partial attempt."""

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import torch
import torch_npu
import vllm_ascend

import test_helper as test


def guard():
    busy = []
    for p in Path('/proc').glob('[0-9]*/maps'):
        if int(p.parent.name) == os.getpid():
            continue
        try:
            loaded = 'libtorch_npu' in p.read_text()
            args = (p.parent / 'cmdline').read_bytes().split(b'\0')
            compiler = args and Path(os.fsdecode(args[0])).name in ('cmake', 'bisheng', 'cc1plus')
        except OSError:
            continue
        if loaded or compiler:
            busy.append(p.parent.name)
    if busy:
        print(json.dumps({'invalid_window': busy}), flush=True)
        raise SystemExit(75)


def configurations(quick):
    counts = (1, 127, 257, 512) if quick else (0, 1, 31, 32, 33, 127, 128, 129, 255, 256, 257, 511, 512)
    for dtype in (torch.float16, torch.bfloat16):
        for rope in (0, 64):
            for count in counts:
                yield dtype, rope, f'selected-{count}', [1], [512], [count], 512
            if not quick:
                yield dtype, rope, 'varlen', [1, 3, 2], [0, 129, 512], [0, 0, 1, 129, 128, 257], 512
                yield dtype, rope, 'pipeline', [7, 28], [4096, 4096], [0, 1, 513, 0, 1025, 2048, 0] * 5, 4096


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--quick', action='store_true')
    parser.add_argument('--measure', action='store_true')
    args = parser.parse_args()
    args.reference.mkdir(exist_ok=True, parents=True)
    assert test.enable_custom_op()
    rows = []
    metadata = dict(variant=args.variant, pid=os.getpid(), device=torch.npu.get_device_name(0),
                    torch_version=torch.__version__, torch_npu_version=torch_npu.__version__,
                    package_path=str(Path(vllm_ascend.__file__).parent),
                    test_sha256=hashlib.sha256(Path(test.__file__).read_bytes()).hexdigest(),
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    for index, (dtype, rope, kind, qlens, kvlens, counts, capacity) in enumerate(configurations(args.quick)):
        guard()
        inputs, expected, lse = test._make_inputs(dtype, rope, qlens, kvlens, counts, kv_capacity=capacity)
        result = test._run(inputs)
        empty_checks = test._check(result, expected, lse)
        actual = [x.cpu() for x in result]
        reference_file = args.reference / f'{index}.pt'
        if args.variant == 'baseline':
            torch.save(actual, reference_file)
        else:
            baseline = torch.load(reference_file, weights_only=True)
            for x, y in zip(actual, baseline, strict=True):
                # Byte comparison also preserves NaN payloads and BF16
                # subnormals in pre-existing empty-row behavior.
                assert torch.equal(x.contiguous().view(torch.uint8), y.contiguous().view(torch.uint8))
        row = dict(index=index, dtype=str(dtype), rope_dim=rope, case=kind, query_lengths=qlens,
                   kv_lengths=kvlens, selected_counts=counts, nonempty_correctness='passed',
                   bitwise_baseline=(args.variant=='candidate'), **empty_checks)
        nonempty = ~torch.isneginf(lse[:, 0])
        error = (actual[0].double()[nonempty] - expected[nonempty]).abs()
        if error.numel():
            relative = error / (expected[nonempty].abs() + 1e-7)
            row.update(max_abs_error=error.max().item(), mean_abs_error=error.mean().item(),
                       mere=relative.mean().item(), mare=relative.max().item())
        if args.measure:
            for _ in range(5):
                test._run(inputs)
            torch.npu.synchronize()
            graph = torch.npu.NPUGraph()
            with torch.npu.graph(graph):
                captured = [test._run(inputs) for _ in range(8)]
            for _ in range(10):
                graph.replay()
            torch.npu.synchronize()
            device_samples, call_samples = [], []
            for _ in range(5):
                guard()
                start, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
                start.record()
                for _ in range(100):
                    graph.replay()
                end.record()
                end.synchronize()
                device_samples.append(start.elapsed_time(end) * 1000 / 800)
                begin = time.perf_counter_ns()
                for _ in range(25):
                    test._run(inputs)
                torch.npu.synchronize()
                call_samples.append((time.perf_counter_ns() - begin) / 1000 / 25)
            row.update(graph_device_us=device_samples, eager_batch_wall_us=call_samples)
            del graph, captured
        guard()
        rows.append(row)
        print(json.dumps(row), flush=True)
        args.output.write_text(json.dumps(dict(metadata=metadata, complete=False, rows=rows), indent=2)+'\n')
    args.output.write_text(json.dumps(dict(metadata=metadata, complete=True, rows=rows), indent=2)+'\n')


if __name__ == '__main__':
    main()
