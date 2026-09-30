"""Native baseline/candidate kernel profiles; no synthetic slow reference."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import torch
import torch_npu

from experiment import guard
import test_helper as test


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--trace-root', type=Path, required=True)
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    args = parser.parse_args()
    assert not args.trace_root.exists(), 'Use a fresh trace directory; retain previous attempts.'
    args.trace_root.mkdir(parents=True)
    assert test.enable_custom_op()
    report = args.trace_root / 'profiler-report.md'
    lines = [f'# Native SFA {args.variant} profiler', '',
             'Independently designed cases from upstream API/tiling/call sites; no generated design.md exists.',
             'CPU + NPU; wait=0, warmup=5, active=5, repeat=1. Sum all op_statistic.csv Total Time(us) rows / 5.',
             f'Cases SHA256: {hashlib.sha256(args.cases.read_bytes()).hexdigest()}', '',
             '| Case | Query shape | DType | RoPE | Selected/query | Native per-step us | CSV |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for index, line in enumerate(args.cases.read_text().splitlines()):
        guard()
        case = json.loads(line)
        values = {x['name']: x.get('value', x.get('shape')) for x in case['inputs']}
        dtype = getattr(torch, case['inputs'][0]['dtype'])
        qlens, kvlens = values['query_lengths'], values['kv_lengths']
        counts = values['selected_counts']
        inputs, output, lse = test._make_inputs(dtype, values['rope_dim'], qlens, kvlens, counts,
                                              kv_capacity=values['kv_capacity'])
        test._check(test._run(inputs), output, lse)
        torch.npu.synchronize()
        trace = args.trace_root / f'case_{index:03d}'
        with torch_npu.profiler.profile(
            activities=[torch_npu.profiler.ProfilerActivity.CPU, torch_npu.profiler.ProfilerActivity.NPU],
            schedule=torch_npu.profiler.schedule(wait=0, warmup=5, active=5, repeat=1),
            on_trace_ready=torch_npu.profiler.tensorboard_trace_handler(str(trace)),
        ) as prof:
            for _ in range(10):
                test._run(inputs)
                prof.step()
        guard()
        csv_files = list(trace.glob('*_ascend_pt/ASCEND_PROFILER_OUTPUT/op_statistic.csv'))
        assert len(csv_files) == 1, csv_files
        with csv_files[0].open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        total_column = next(x for x in rows[0] if x.replace(' ', '').lower() == 'totaltime(us)')
        total = sum(float(row[total_column]) for row in rows) / 5
        print(f'{args.variant} case {index}: {total:.6f} us', flush=True)
        lines.append(f'| {index} | {values["query"]} | {dtype} | {values["rope_dim"]} | {counts} | {total:.6f} | {csv_files[0].relative_to(args.trace_root)} |')
        report.write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
