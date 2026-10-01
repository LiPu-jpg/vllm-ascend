"""Locate byte differences in every legacy layout/block coverage case."""

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import torch
import torch_npu  # noqa: F401

from experiment import guard
from vllm_ascend.utils import enable_custom_op


def describe_difference(actual, reference, expected_shape, counts):
    actual = actual.contiguous().reshape(expected_shape)
    reference = reference.contiguous().reshape(expected_shape)
    assert actual.dtype == reference.dtype
    byte_difference = actual.view(torch.uint8) != reference.view(torch.uint8)
    different = byte_difference.reshape(*actual.shape, actual.element_size()).any(-1)
    valid = torch.tensor(counts).gt(0).reshape(len(counts), *([1] * (actual.ndim - 1))).expand_as(actual)
    coordinates = different.nonzero()[:8].tolist()
    examples = []
    for coordinate in coordinates:
        key = tuple(coordinate)
        examples.append(dict(coordinate=coordinate, selected_count=counts[coordinate[0]],
                             actual=repr(actual[key].item()), reference=repr(reference[key].item())))
    return dict(bitwise_equal=not different.any().item(),
                differing_nonempty_elements=(different & valid).sum().item(),
                differing_empty_elements=(different & ~valid).sum().item(),
                examples=examples)


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--coverage-source', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    tensors = args.output.with_suffix('')
    tensors.mkdir()
    spec = importlib.util.spec_from_file_location('legacy_coverage_probe', args.coverage_source)
    coverage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(coverage)
    assert enable_custom_op()
    rows = []
    configs = itertools.product((torch.float16, torch.bfloat16), (0, 64),
                                ('PA_BSND', 'TND', 'BSND'), (1, 2, 4, 8), (0, 3))
    for index, (dtype, rope, layout, block, mode) in enumerate(configs):
        guard()
        heads = {1: 64, 2: 8, 4: 128, 8: 1}[block]
        inputs, expected, lse, counts = coverage.make_case(dtype, rope, layout, block, mode, heads)
        frozen_path = args.reference / f'{index}.pt'
        frozen = torch.load(frozen_path, weights_only=True)
        result = torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)
        actual = [x.cpu() for x in result]
        error = None
        try:
            coverage.check(result, expected, lse)
        except AssertionError as exc:
            error = str(exc)
        second = [x.cpu() for x in torch.ops._C_ascend.npu_sparse_flash_attention(**inputs)]
        shapes = [expected.shape, lse.shape, lse.shape]
        against_frozen = [describe_difference(x, y, s, counts)
                          for x, y, s in zip(actual, frozen, shapes, strict=True)]
        within_process = [describe_difference(x, y, s, counts)
                          for x, y, s in zip(actual, second, shapes, strict=True)]
        row = dict(index=index, dtype=str(dtype), rope_dim=rope, layout=layout,
                   sparse_block_size=block, sparse_mode=mode, heads=heads,
                   selected_tokens=counts, nonempty_reference='passed' if error is None else 'failed',
                   reference_error=error, frozen_sha256=hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
                   against_frozen=against_frozen, repeat_within_process=within_process)
        if any(not d['bitwise_equal'] for d in against_frozen + within_process):
            p = tensors / f'{index}.pt'
            torch.save(dict(first=actual, second=second, frozen=frozen, expected=expected, lse=lse, counts=counts), p)
            row['diagnostic_tensor_sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
        rows.append(row)
        guard()
        args.output.write_text(json.dumps(dict(complete=False, rows=rows), indent=2) + '\n')
        print(json.dumps(row), flush=True)
    args.output.write_text(json.dumps(dict(complete=True, variant=args.variant, rows=rows,
                          script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                          coverage_source_sha256=hashlib.sha256(args.coverage_source.read_bytes()).hexdigest(),
                          torch_version=torch.__version__, torch_npu_version=torch_npu.__version__), indent=2) + '\n')


if __name__ == '__main__':
    main()
