"""Controlled production HcPre calls to identify HF32 fractional-bit retention.

This is diagnostic evidence, not a replacement oracle or a performance test.
The original 28-case failures and thresholds remain unchanged.
"""
import hashlib
import json
import os
from pathlib import Path

import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op

assert enable_custom_op()
torch_npu.npu.config.allow_internal_format = True
torch.set_num_threads(1)
result = Path(os.environ['FULL_RESULT_DIR'])
data = result / 'data'
data.mkdir()
rows = []
with torch.inference_mode():
    for hidden in (4096, 7168):
        for bit in (7, 10, 11, 12, 15, 18, 19, 20, 23):
            x = torch.zeros(1, 4, hidden, dtype=torch.bfloat16)
            x[0, 0, 0] = 1
            fn = torch.zeros(24, 4 * hidden)
            coefficients = torch.tensor([1., 1. + 2. ** -bit, -1., -(1. + 2. ** -bit)])
            fn[:4, 0] = coefficients
            inverse = torch.rsqrt(x.float().flatten(-2).square().mean(-1) + 1e-6)
            scale = torch.ones(3)
            base = torch.zeros(24)
            base[:4] = torch.tensor([-1., -1., 1., 1.]) * inverse
            inputs = tuple(t.npu() for t in (x, fn, scale, base))
            outputs = torch.ops._C_ascend.npu_hc_pre_v3(
                *inputs, None, hc_mult=4, hc_sinkhorn_iters=20, norm_eps=1e-6, hc_eps=1e-6)
            cpu = tuple(t.cpu() for t in outputs)
            assert all(torch.isfinite(t).all() for t in cpu)
            references = {}
            for mantissa in (10, 11, 19, 23):
                mask = ~((1 << (23 - mantissa)) - 1)
                quantized = (coefficients.view(torch.int32) & mask).view(torch.float32)
                expected = torch.sigmoid(quantized * inverse + base[:4]) + 1e-6
                references[str(mantissa)] = {'pre': expected.tolist(),
                    'max_abs_difference': (cpu[3].reshape(-1) - expected).abs().max().item()}
            key = f'd{hidden}-bit{bit}'
            torch.save({'inputs': (x, fn, scale, base), 'outputs': cpu}, data / f'{key}.pt')
            row = {'case': key, 'controlled_coefficients': coefficients.tolist(),
                   'actual_pre': cpu[3].reshape(-1).tolist(), 'rtz_reference_variants': references}
            rows.append(row)
            (data / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
            print('CONTROLLED_HF32_BIT_RESULT', key, row, flush=True)
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
print('HF32_BIT_DIAGNOSTIC_COMPLETE', len(rows), flush=True)
