"""Retain the earlier partial-block failures and check exact output parity."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import torch
import torch_npu  # noqa: F401
import vllm_ascend

from experiment import guard
from paired import digest_inputs


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    args.reference.mkdir(parents=True, exist_ok=True)
    helper = Path(__file__).with_name('test_sparse_flash_attention_index_staging.py')
    spec = importlib.util.spec_from_file_location('partial_block_helper', helper)
    edge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(edge)
    assert edge.enable_custom_op()
    rows = []
    metadata = dict(variant=args.variant, package_path=str(Path(vllm_ascend.__file__).parent),
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    helper_sha256=hashlib.sha256(helper.read_bytes()).hexdigest())

    def check(kind, dtype, capacity, block, mode, inputs, cpu, outputs):
        guard()
        index = len(rows)
        digest = digest_inputs(inputs)
        actual = [x.cpu() for x in outputs]
        error = None
        try:
            edge.check_outputs(outputs, cpu, block, mode)
        except AssertionError as exc:
            error = str(exc)
        path = args.reference/f'{index}.pt'
        if args.variant == 'baseline':
            assert not path.exists()
            torch.save(dict(input_sha256=digest,outputs=actual,reference_passed=error is None),path)
        else:
            previous = torch.load(path,weights_only=True)
            assert previous['input_sha256'] == digest
            assert all(torch.equal(x.contiguous().view(torch.uint8), y.contiguous().view(torch.uint8))
                       for x,y in zip(actual,previous['outputs'],strict=True)), index
            assert previous['reference_passed'] == (error is None), index
        rows.append(dict(index=index,kind=kind,dtype=str(dtype),capacity=capacity,block=block,mode=mode,
                         input_sha256=digest,bytewise_parity='captured' if args.variant=='baseline' else 'passed',
                         reference_passed=error is None,reference_error=error))
        args.output.write_text(json.dumps(dict(metadata=metadata,complete=False,rows=rows),indent=2)+'\n')

    for dtype in (torch.float16,torch.bfloat16):
        for capacity in (1,3,17,257,513):
            for block in (1,2,4):
                for mode in (0,3):
                    guard()
                    inputs,cpu = edge.make_inputs(dtype,capacity,block,mode)
                    outputs = torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)
                    check('eager',dtype,capacity,block,mode,inputs,cpu,outputs)
        for block in (1,2,4):
            guard()
            inputs,cpu = edge.make_inputs(dtype,513,block,0)
            for _ in range(3):torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)
            torch.npu.synchronize()
            graph = torch.npu.NPUGraph()
            with torch.npu.graph(graph):
                outputs = torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)
            for count in (1,17,513):
                guard()
                changed = cpu['indices'].clone()
                changed[...,count:] = -1
                inputs['sparse_indices'].copy_(changed.npu())
                graph.replay()
                torch.npu.synchronize()
                check(f'graph-count-{count}',dtype,513,block,0,inputs,{**cpu,'indices':changed},outputs)
            del graph
    guard()
    args.output.write_text(json.dumps(dict(metadata=metadata,complete=True,rows=rows),indent=2)+'\n')


if __name__ == '__main__':
    main()
