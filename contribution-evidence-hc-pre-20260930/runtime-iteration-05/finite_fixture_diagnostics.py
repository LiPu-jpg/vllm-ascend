"""Diagnose all 72 frozen nightly fixtures without short-circuiting CPU failures."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op


def bits_equal(left, right):
    return torch.equal(left.view(torch.uint8), right.view(torch.uint8))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--oracle', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    assert enable_custom_op()
    torch_npu.npu.config.allow_internal_format = True
    torch.set_num_threads(1)
    path = args.oracle
    spec = importlib.util.spec_from_file_location('unchanged_cpu_oracle', path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    rows = []
    with torch.inference_mode():
        for hidden in (128, 4096, 7168):
            for batch_shape in ((1,), (17,), (257,), (3, 17)):
                for signed in (False, True):
                    for iters in (1, 3, 20):
                        batch_key = 'x'.join(map(str, batch_shape))
                        key = f'b{batch_key}-d{hidden}-signed{int(signed)}-i{iters}'
                        x, fn, scale, base = oracle._make_hc_pre_inputs((*batch_shape, 4, hidden))
                        if signed:
                            x = (x.float() - 1).bfloat16()
                            fn = fn - 0.5 / (4 * hidden)
                            base = torch.linspace(-3, 3, 24)
                        cpu_inputs = (x, fn, scale, base)
                        expected = oracle._hc_pre_cpu(*cpu_inputs, sinkhorn_iters=iters)
                        inputs = tuple(t.npu() for t in cpu_inputs)
                        originals = tuple(t.clone() for t in inputs)

                        def call_v2():
                            return torch.ops._C_ascend.npu_hc_pre_v2(*inputs, 4, iters, 1e-6, 1e-6)

                        def call_v3():
                            return torch.ops._C_ascend.npu_hc_pre_v3(
                                *inputs, None, hc_mult=4, hc_sinkhorn_iters=iters, norm_eps=1e-6, hc_eps=1e-6)

                        row = {'case': key, 'cpu_accuracy_pass': False, 'errors': [], 'cpu_errors': [],
                               'shape': list(x.shape), 'cpu_metrics': [], 'input_sha256': [hashlib.sha256(t.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
                                                for t in cpu_inputs]}
                        try:
                            actual = call_v2()
                            repeated = call_v2()
                            v3 = call_v3()
                            graph = torch.npu.NPUGraph()
                            with torch.npu.graph(graph):
                                captured = call_v2()
                            graph.replay()
                            torch.npu.synchronize()
                            for kind, compared in (('repeat', repeated), ('v3', v3[:3]), ('graph', captured)):
                                for index, (left, right) in enumerate(zip(actual, compared, strict=True)):
                                    if not bits_equal(left, right):
                                        row['errors'].append(f'{kind}:{index}')
                            cpu = {'v2': tuple(t.cpu() for t in actual), 'v3': tuple(t.cpu() for t in v3)}
                            for api, values in cpu.items():
                                for index, (left, right) in enumerate(zip(values, expected[:len(values)], strict=True)):
                                    diff = (left.float() - right.float()).abs()
                                    threshold = oracle.Y_DIFF_THRESHOLD if index == 0 else oracle.AUX_DIFF_THRESHOLD
                                    magnitude = torch.maximum(left.float().abs(), right.float().abs())
                                    close = (diff <= threshold) | (diff / magnitude.clamp_min(torch.finfo(torch.float32).tiny) <= threshold)
                                    row['cpu_metrics'].append({'api': api, 'output': index,
                                        'pass_rate': close.float().mean().item(),
                                        'max_abs_diff': diff.max().item(),
                                        'actual_nonfinite': int((~torch.isfinite(left)).sum()),
                                        'expected_nonfinite': int((~torch.isfinite(right)).sum())})
                                    try:
                                        oracle._assert_close_with_pass_rate(
                                            left, right,
                                            diff_threshold=oracle.Y_DIFF_THRESHOLD if index == 0 else oracle.AUX_DIFF_THRESHOLD,
                                            required_pass_rate=oracle.Y_REQUIRED_PASS_RATE if index == 0 else oracle.AUX_REQUIRED_PASS_RATE)
                                    except AssertionError as error:
                                        row['cpu_errors'].append(f'{api}:{index}:{error}')
                            row['cpu_accuracy_pass'] = not row['cpu_errors']
                            for left, right in zip(inputs, originals, strict=True):
                                if not bits_equal(left, right):
                                    row['errors'].append('input changed')
                            if args.reference:
                                ref = torch.load(args.reference / f'{key}.pt', weights_only=True)
                                for api, values in cpu.items():
                                    for index, (left, right) in enumerate(zip(values, ref[api], strict=True)):
                                        if not bits_equal(left, right):
                                            row['errors'].append(f'baseline:{api}:{index}')
                            destination = args.output / f'{key}.pt'
                            torch.save({**cpu, 'expected': expected}, destination)
                            row['sha256'] = hashlib.sha256(destination.read_bytes()).hexdigest()
                            del graph
                        except Exception as error:
                            row['errors'].append(f'{type(error).__name__}:{error}')
                        rows.append(row)
                        (args.output / 'results.json').write_text(json.dumps(rows, indent=2))
                        print(key, row, flush=True)
    print('FIXTURE_DIAGNOSTIC_COUNTS', len(rows), 'cpu_pass', sum(r['cpu_accuracy_pass'] for r in rows),
          'other_fail', sum(bool(r['errors']) for r in rows), flush=True)
    raise SystemExit(any(not r['cpu_accuracy_pass'] or r['errors'] for r in rows))


if __name__ == '__main__':
    main()
