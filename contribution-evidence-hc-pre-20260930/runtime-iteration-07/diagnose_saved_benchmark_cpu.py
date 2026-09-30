"""CPU-only sensitivity analysis of frozen outputs; does not certify a new oracle.

Reproduce original expected tensors byte for byte and inputs by their saved
hashes before evaluating alternative HF32 models. Preserve every failed case.
"""
import argparse
import hashlib
import json
from pathlib import Path

import torch
import torch.nn.functional as F


def quantize(values, width, mode):
    drop = 23 - width
    bits = values.contiguous().view(torch.int32)
    if mode == 'nearest-away':
        bits = bits + (1 << (drop - 1))
    elif mode == 'nearest-even':
        bits = bits + (1 << (drop - 1)) - 1 + ((bits >> drop) & 1)
    return (bits & ~((1 << drop) - 1)).view(torch.float32)


def reference(x, fn, scale, base, width, mode):
    x_float = x.float()
    x_flat = x_float.flatten(-2)
    inverse = torch.rsqrt(x_flat.square().mean(-1, keepdim=True) + 1e-6)
    mixes = F.linear(quantize(x_flat, width, mode), quantize(fn, width, mode)) * inverse
    pre, post, comb = mixes.split([4, 4, 16], dim=-1)
    comb = comb.unflatten(-1, (4, 4))
    pre = torch.sigmoid(pre * scale[0] + base[:4]) + 1e-6
    post = 2 * torch.sigmoid(post * scale[1] + base[4:8])
    comb = comb * scale[2] + base[8:].view(4, 4)
    comb = comb.softmax(-1) + 1e-6
    comb = comb / (comb.sum(-2, keepdim=True) + 1e-6)
    for _ in range(19):
        comb = comb / (comb.sum(-1, keepdim=True) + 1e-6)
        comb = comb / (comb.sum(-2, keepdim=True) + 1e-6)
    y = (pre.unsqueeze(-1) * x_float).sum(dim=-2).to(x.dtype)
    return y, post, comb, pre


def make_inputs(tokens, hidden, signed):
    generator = torch.Generator().manual_seed(1024)
    fan_in = 4 * hidden
    x = (torch.rand(tokens, 4, hidden, generator=generator) * 2).bfloat16()
    fn = torch.rand(24, fan_in, generator=generator) / fan_in
    scale = torch.rand(3, generator=generator) * 2
    base = torch.rand(24, generator=generator) * 2
    if signed:
        x = (x.float() - 1).bfloat16()
        fn = (fn - 0.5 / fan_in) * fan_in**0.5
        base = torch.linspace(-3, 3, 24)
    return x, fn, scale, base


def metric(actual, expected, index):
    left, right = actual.float(), expected.float()
    diff = (left - right).abs()
    threshold = 4e-3 if index == 0 else 1e-4
    required = .98 if index == 0 else .995
    magnitude = torch.maximum(left.abs(), right.abs())
    close = (diff <= threshold) | (diff / magnitude.clamp_min(torch.finfo(torch.float32).tiny) <= threshold)
    pass_rate = close.float().mean().item()
    return {'output': index, 'pass_rate': pass_rate, 'max_abs_diff': diff.max().item(),
            'threshold': threshold, 'required_pass_rate': required,
            'pass': pass_rate >= required, 'actual_nonfinite': int((~torch.isfinite(left)).sum()),
            'expected_nonfinite': int((~torch.isfinite(right)).sum())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--iteration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    torch.set_num_threads(1)
    rows = []
    with torch.inference_mode():
        for variant in ('baseline', 'candidate'):
            data = args.iteration / f'prefetch1-benchmark-fixture-{variant}' / 'data'
            original_rows = json.loads((data / 'results.json').read_text())
            assert len(original_rows) == 28
            for original in original_rows:
                key = original['case']
                tokens, hidden, signed = key.split('-')
                inputs = make_inputs(int(tokens[1:]), int(hidden[1:]), bool(int(signed[6:])))
                hashes = [hashlib.sha256(t.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest() for t in inputs]
                assert hashes == original['input_sha256'], key
                saved_path = data / f'{key}.pt'
                assert hashlib.sha256(saved_path.read_bytes()).hexdigest() == original['sha256'], key
                saved = torch.load(saved_path, weights_only=True)
                expected_original = reference(*inputs, 10, 'rtz')
                assert all(torch.equal(a.view(torch.uint8), b.view(torch.uint8))
                           for a, b in zip(expected_original, saved['expected'], strict=True)), key
                models = {}
                for width, mode in [(10, 'rtz'), (11, 'rtz'), (11, 'nearest-even'), (11, 'nearest-away')]:
                    expected = reference(*inputs, width, mode)
                    metrics = []
                    for api in ('v2', 'v3'):
                        for i, actual in enumerate(saved[api]):
                            metrics.append({'api': api, **metric(actual, expected[i], i)})
                    models[f'{width}-{mode}'] = {'all_outputs_pass': all(m['pass'] for m in metrics), 'metrics': metrics}
                assert models['10-rtz']['all_outputs_pass'] == original['cpu_accuracy_pass'], key
                row = {'variant': variant, 'case': key, 'input_sha256_verified': hashes,
                       'original_expected_byte_reproduced': True, 'saved_tensor_sha256': original['sha256'],
                       'retained_original_errors': original['errors'], 'models': models}
                rows.append(row)
                (args.output / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
                print('SAVED_BENCHMARK_CPU_DIAGNOSTIC', variant, key,
                      {name: model['all_outputs_pass'] for name, model in models.items()}, flush=True)
    summary = {'scope': 'Independent CPU sensitivity analysis, not NPU revalidation or performance',
               'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'cases': len(rows),
               'counts': {variant: {name: sum(r['models'][name]['all_outputs_pass'] for r in rows if r['variant'] == variant)
                         for name in rows[0]['models']} for variant in ('baseline', 'candidate')}}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
