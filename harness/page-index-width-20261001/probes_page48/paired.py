"""Balanced-process native benchmark with preserved raw device/wall samples."""

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import torch
import torch_npu
import vllm_ascend

from experiment import guard
import test_helper as test


def digest_inputs(inputs):
    digest = hashlib.sha256()
    for name, value in sorted(inputs.items()):
        digest.update(name.encode())
        if isinstance(value, torch.Tensor):
            cpu = value.cpu().contiguous()
            digest.update(str((cpu.dtype, tuple(cpu.shape))).encode())
            digest.update(cpu.view(torch.uint8).numpy().tobytes())
        else:
            digest.update(str(value).encode())
    return digest.hexdigest()


def measure(inputs):
    for _ in range(5):
        test._run(inputs)
    torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    with torch.npu.graph(graph):
        outputs = [test._run(inputs) for _ in range(8)]
    for _ in range(10):
        graph.replay()
    torch.npu.synchronize()
    device, wall = [], []
    for _ in range(5):
        guard()
        start, end = torch.npu.Event(enable_timing=True), torch.npu.Event(enable_timing=True)
        start.record()
        for _ in range(100):
            graph.replay()
        end.record()
        end.synchronize()
        device.append(start.elapsed_time(end) * 1000 / 800)
        begin = time.perf_counter_ns()
        for _ in range(25):
            test._run(inputs)
        torch.npu.synchronize()
        wall.append((time.perf_counter_ns() - begin) / 1000 / 25)
    guard()
    del graph, outputs
    return device, wall


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    args.reference.mkdir(parents=True, exist_ok=True)
    assert test.enable_custom_op()
    metadata = dict(variant=args.variant, pid=os.getpid(), device=torch.npu.get_device_name(0),
                    torch_version=torch.__version__, torch_npu_version=torch_npu.__version__,
                    package_path=str(Path(vllm_ascend.__file__).parent),
                    cases_sha256=hashlib.sha256(args.cases.read_bytes()).hexdigest(),
                    test_sha256=hashlib.sha256(Path(test.__file__).read_bytes()).hexdigest(),
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    rows = []
    for index, line in enumerate(args.cases.read_text().splitlines()):
        guard()
        case = json.loads(line)
        values = {x['name']: x.get('value', x.get('shape')) for x in case['inputs']}
        dtype = getattr(torch, case['inputs'][0]['dtype'])
        inputs, expected, lse = test._make_inputs(dtype, values['rope_dim'], values['query_lengths'],
                                                values['kv_lengths'], values['selected_counts'],
                                                kv_capacity=values['kv_capacity'])
        result = test._run(inputs)
        diagnostics = test._check(result, expected, lse)
        actual = [x.cpu() for x in result]
        input_digest = digest_inputs(inputs)
        path = args.reference / f'{index}.pt'
        if args.variant == 'baseline' and not path.exists():
            torch.save(dict(input_sha256=input_digest, outputs=actual), path)
        else:
            old = torch.load(path, weights_only=True)
            assert old['input_sha256'] == input_digest
            for x, y in zip(actual, old['outputs'], strict=True):
                assert torch.equal(x.contiguous().view(torch.uint8), y.contiguous().view(torch.uint8)), index
        device, wall = measure(inputs)
        row = dict(index=index, query_shape=values['query'], dtype=str(dtype), rope_dim=values['rope_dim'],
                   selected_counts=values['selected_counts'], input_sha256=input_digest,
                   nonempty_reference='passed', bytewise_reference='passed',
                   graph_device_us=device, eager_batch_wall_us=wall, **diagnostics)
        rows.append(row)
        print(json.dumps(row), flush=True)
        args.output.write_text(json.dumps(dict(metadata=metadata, complete=False, rows=rows), indent=2)+'\n')
    guard()
    args.output.write_text(json.dumps(dict(metadata=metadata, complete=True, rows=rows), indent=2)+'\n')


if __name__ == '__main__':
    main()
