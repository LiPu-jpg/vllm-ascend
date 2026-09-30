"""Independent layout/block/mode coverage and production dispatch check."""

import argparse
import itertools
import json
from pathlib import Path
from types import SimpleNamespace

import torch
import torch_npu  # noqa: F401

from experiment import guard
from vllm_ascend.utils import enable_custom_op


def make_case(dtype, rope_dim, layout, sparse_block_size, mode, heads):
    torch.manual_seed(930)
    qlens = [2, 2] if layout == 'BSND' else [1, 3, 2]
    kvlens = [512, 1024] if layout == 'BSND' else [256, 512, 1024]
    batch, capacity, page_size = len(qlens), 1024, 128
    query = torch.randn(sum(qlens), heads, 512, dtype=dtype)
    query_rope = torch.randn(sum(qlens), heads, rope_dim, dtype=dtype) if rope_dim else None
    key = torch.randn(batch, capacity, 1, 512, dtype=dtype)
    key_rope = torch.randn(batch, capacity, 1, rope_dim, dtype=dtype) if rope_dim else None
    indices = torch.full((sum(qlens), 1, 2048), -1, dtype=torch.int32)
    expected = torch.zeros(sum(qlens), heads, 512, dtype=torch.float64)
    expected_lse = torch.full((sum(qlens), heads), -torch.inf, dtype=torch.float64)
    actual_counts, token = [], 0
    for request, qlen in enumerate(qlens):
        for position in range(qlen):
            visible = kvlens[request] if mode == 0 else kvlens[request] - qlen + position + 1
            blocks = visible // sparse_block_size
            count = min((0, 1, 33, 127, 257, 512)[token], blocks)
            selected_blocks = torch.randperm(blocks)[:count].sort().values
            indices[token, 0, :count] = selected_blocks.int()
            selected = (selected_blocks[:, None] * sparse_block_size + torch.arange(sparse_block_size)).reshape(-1)
            actual_counts.append(len(selected))
            if count:
                logits = query[token].double() @ key[request, selected, 0].double().T
                if rope_dim:
                    logits += query_rope[token].double() @ key_rope[request, selected, 0].double().T
                logits /= 24
                expected[token] = logits.softmax(-1) @ key[request, selected, 0].double()
                expected_lse[token] = logits.logsumexp(-1)
            token += 1
    if layout == 'PA_BSND':
        order = torch.randperm(batch * (capacity // page_size))
        table = order.reshape(batch, -1).int()
        physical = torch.empty(batch * (capacity // page_size), page_size, 1, 512, dtype=dtype)
        physical[order] = key.reshape(-1, page_size, 1, 512)
        if rope_dim:
            physical_rope = torch.empty(*physical.shape[:-1], rope_dim, dtype=dtype)
            physical_rope[order] = key_rope.reshape(-1, page_size, 1, rope_dim)
            key_rope = physical_rope
        key = physical
    else:
        table = None
        if layout == 'TND':
            key = torch.cat([key[b, :length] for b, length in enumerate(kvlens)])
            if rope_dim:
                key_rope = torch.cat([key_rope[b, :length] for b, length in enumerate(kvlens)])
        else:
            query = query.reshape(batch, qlens[0], heads, 512)
            indices = indices.reshape(batch, qlens[0], 1, -1)
            if rope_dim:
                query_rope = query_rope.reshape(batch, qlens[0], heads, rope_dim)
    query_layout = 'BSND' if layout == 'BSND' else 'TND'
    inputs = dict(query=query.npu(), key=key.npu(), sparse_indices=indices.npu(),
                  block_table=table.npu() if table is not None else None,
                  actual_seq_lengths_query=(torch.tensor(qlens, dtype=torch.int32) if layout == 'BSND'
                                            else torch.tensor(qlens, dtype=torch.int32).cumsum(0).int()).npu(),
                  actual_seq_lengths_kv=(torch.tensor(kvlens, dtype=torch.int32).cumsum(0).int() if layout == 'TND'
                                         else torch.tensor(kvlens, dtype=torch.int32)).npu(),
                  query_rope=query_rope.npu() if rope_dim else None,
                  key_rope=key_rope.npu() if rope_dim else None,
                  scale_value=1/24, sparse_block_size=sparse_block_size, sparse_mode=mode, attention_mode=2,
                  layout_query=query_layout, layout_kv=layout, return_softmax_lse=True)
    inputs['value'] = inputs['key']
    return inputs, expected, expected_lse, actual_counts


def check(result, expected, expected_lse):
    output, maximum, total = [x.cpu().double() for x in result]
    output = output.reshape_as(expected)
    # Both layouts put the KV-head dimension before query heads in LSE.
    lse = (maximum + total.log()).reshape_as(expected_lse)
    valid = torch.isfinite(expected_lse[:, 0])
    torch.testing.assert_close(output[valid], expected[valid], atol=0.03, rtol=0.01)
    torch.testing.assert_close(lse[valid], expected_lse[valid], atol=0.005, rtol=0.001)
    return [x.cpu() for x in result]


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    args = parser.parse_args()
    args.reference.mkdir(parents=True, exist_ok=True)
    assert enable_custom_op()
    rows = []
    configs = itertools.product((torch.float16, torch.bfloat16), (0, 64),
                                ('PA_BSND', 'TND', 'BSND'), (1, 2, 4, 8), (0, 3))
    for index, (dtype, rope, layout, block, mode) in enumerate(configs):
        guard()
        heads = {1:64, 2:8, 4:128, 8:1}[block]
        inputs, expected, lse, counts = make_case(dtype, rope, layout, block, mode, heads)
        result = torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)
        actual = [x.cpu() for x in result]
        reference_error = None
        try:
            check(result, expected, lse)
        except AssertionError as exc:
            reference_error = str(exc)
        path = args.reference / f'{index}.pt'
        if args.variant == 'baseline':
            torch.save(actual, path)
        identical = None
        if args.variant == 'candidate':
            identical = [torch.equal(x.contiguous().view(torch.uint8), y.contiguous().view(torch.uint8))
                         for x, y in zip(actual, torch.load(path, weights_only=True), strict=True)]
        guard()
        row = dict(index=index, dtype=str(dtype), rope_dim=rope, layout=layout,
                   sparse_block_size=block, sparse_mode=mode, heads=heads, selected_tokens=counts,
                   nonempty_reference='passed' if reference_error is None else 'failed',
                   reference_error=reference_error, bytewise_baseline_by_output=identical)
        rows.append(row)
        print(json.dumps(row), flush=True)
        args.output.write_text(json.dumps(dict(complete=False, rows=rows), indent=2)+'\n')
    # Import and invoke the actual production dispatcher, with real NPU tensors.
    from vllm_ascend.device.device_op import BaseDeviceAdaptor
    for mode in (0, 3):
        guard()
        inputs, expected, lse, _ = make_case(torch.bfloat16, 64, 'PA_BSND', 1, mode, 64)
        actual = BaseDeviceAdaptor.execute_sparse_flash_attention_process(
            SimpleNamespace(scale=1/24), inputs['query'], inputs['query_rope'],
            (inputs['key'], inputs['key_rope']), inputs['sparse_indices'],
            SimpleNamespace(block_table=inputs['block_table']), inputs['actual_seq_lengths_query'],
            inputs['actual_seq_lengths_kv'], sparse_mode=mode, return_lse=True)
        check(actual, expected, lse)
        native = torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)
        for x, y in zip(actual, native, strict=True):
            assert torch.equal(x.cpu().contiguous().view(torch.uint8), y.cpu().contiguous().view(torch.uint8))
        rows.append(dict(dispatch='BaseDeviceAdaptor.execute_sparse_flash_attention_process',
                         sparse_mode=mode, reference='passed', bitwise_native=True))
    guard()
    args.output.write_text(json.dumps(dict(complete=True, rows=rows), indent=2)+'\n')


if __name__ == '__main__':
    main()
