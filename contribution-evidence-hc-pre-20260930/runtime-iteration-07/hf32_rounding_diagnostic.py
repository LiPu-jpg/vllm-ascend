"""Independent production HF32 rounding controls; no oracle or threshold changes."""
import hashlib
import json
import os
from pathlib import Path

import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op


def quantize(values, fractional_bits, rounding):
    drop = 23 - fractional_bits
    bits = values.view(torch.int32)
    if rounding == 'nearest-away':
        bits = bits + (1 << (drop - 1))
    elif rounding == 'nearest-even':
        bits = bits + (1 << (drop - 1)) - 1 + ((bits >> drop) & 1)
    return (bits & ~((1 << drop) - 1)).view(torch.float32)


assert enable_custom_op()
torch_npu.npu.config.allow_internal_format = True
torch.set_num_threads(1)
result = Path(os.environ['FULL_RESULT_DIR'])
data = result / 'data'
data.mkdir()
rows = []
ulp = 2. ** -11
offsets = [('zero', 0.), ('quarter', ulp / 4),
           ('below-half', ulp / 2 - 2. ** -23), ('half', ulp / 2),
           ('above-half', ulp / 2 + 2. ** -23), ('three-quarter', 3 * ulp / 4),
           ('next-grid', ulp)]
with torch.inference_mode():
    for hidden in (4096, 7168):
        for anchor_label, anchor in [('even', 1.), ('odd', 1. + ulp),
                                     ('exponent-carry', 2. - ulp)]:
            for offset_label, offset in offsets:
                x = torch.zeros(1, 4, hidden, dtype=torch.bfloat16)
                x[0, 0, 0] = 1
                coefficients = torch.tensor([anchor, anchor + offset, -anchor, -(anchor + offset)])
                fn = torch.zeros(24, 4 * hidden)
                fn[:4, 0] = coefficients
                inverse = torch.rsqrt(x.float().flatten(-2).square().mean(-1) + 1e-6)
                scale = torch.ones(3)
                base = torch.zeros(24)
                base[:4] = torch.tensor([-anchor, -anchor, anchor, anchor]) * inverse
                inputs = tuple(t.npu() for t in (x, fn, scale, base))
                outputs = torch.ops._C_ascend.npu_hc_pre_v3(
                    *inputs, None, hc_mult=4, hc_sinkhorn_iters=20, norm_eps=1e-6, hc_eps=1e-6)
                cpu = tuple(t.cpu() for t in outputs)
                references = {}
                for width, rounding in [(10, 'rtz'), (11, 'rtz'), (11, 'nearest-even'),
                                        (11, 'nearest-away'), (19, 'rtz'), (23, 'rtz')]:
                    rounded = coefficients if width == 23 else quantize(coefficients, width, rounding)
                    expected = torch.sigmoid(rounded * inverse + base[:4]) + 1e-6
                    references[f'{width}-{rounding}'] = {
                        'rounded_coefficients': rounded.tolist(), 'pre': expected.tolist(),
                        'max_abs_difference': (cpu[3].reshape(-1) - expected).abs().max().item()}
                key = f'd{hidden}-{anchor_label}-{offset_label}'
                destination = data / f'{key}.pt'
                torch.save({'inputs': (x, fn, scale, base), 'outputs': cpu}, destination)
                row = {'case': key, 'coefficients': coefficients.tolist(),
                       'all_outputs_finite': all(bool(torch.isfinite(t).all()) for t in cpu),
                       'actual_pre': cpu[3].reshape(-1).tolist(), 'references': references,
                       'tensor_sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
                rows.append(row)
                (data / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
                print('CONTROLLED_HF32_ROUNDING_RESULT', key, row, flush=True)
trace = Path(os.environ['HC_PRE_FILE_TRACE'])
records = []
for line in trace.read_text().splitlines():
    operation, fd, name = line.split('\t', 2)
    path = Path(name)
    if int(fd) >= 0 and path.suffix == '.o' and path.exists():
        records.append({'operation': operation, 'path': name,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
(result / 'opened-kernels.json').write_text(json.dumps(records, indent=2) + '\n')
assert records, 'Actual object selection remains unproven'
assert len(rows) == 42
print('HF32_ROUNDING_DIAGNOSTIC_COMPLETE', len(rows), flush=True)
