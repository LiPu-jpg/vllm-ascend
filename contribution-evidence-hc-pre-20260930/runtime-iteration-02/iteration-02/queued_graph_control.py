"""Matched diagnostics of historical probe vs actual production registration.

Only production mode is plugin integration. No source, loader, registration,
benchmark function or oracle is monkeypatched. Kernel and registration factors
are varied in separate processes; all warmups and observations are retained.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import statistics
import time
from pathlib import Path

import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op


def measure_queued_graph(inputs, samples, warmup, graph_batch):
    """Amortize the external event-to-host-submit gap over queued replays.

    Capture the same 20 complete HcPre calls as benchmark.measure, then queue
    several replays between each event pair without an intervening host sync.
    This is a separate steady queued-graph measurement, not model throughput.
    """
    def call():
        return torch.ops._C_ascend.npu_hc_pre_v3(
            *inputs, None, hc_mult=4, hc_sinkhorn_iters=20, norm_eps=1e-6, hc_eps=1e-6
        )

    for _ in range(3):
        outputs = call()
    torch.npu.synchronize()
    graph = torch.npu.NPUGraph()
    with torch.npu.graph(graph):
        for _ in range(20):
            outputs = call()
    count = 20 * graph_batch
    events, walls = [], []
    for _ in range(warmup + samples):
        start = torch.npu.Event(enable_timing=True)
        end = torch.npu.Event(enable_timing=True)
        torch.npu.synchronize()
        begin = time.perf_counter_ns()
        start.record()
        for _ in range(graph_batch):
            graph.replay()
        end.record()
        torch.npu.synchronize()
        walls.append((time.perf_counter_ns() - begin) / (1000 * count))
        events.append(start.elapsed_time(end) * 1000 / count)
    return tuple(t.cpu() for t in outputs), events, walls


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--registration',choices=('production','historical-probe'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',type=Path)
    parser.add_argument('--warmup',type=int,default=20)
    parser.add_argument('--samples',type=int,default=50)
    parser.add_argument('--rounds',type=int,default=3)
    parser.add_argument('--timing',choices=('graph','event'),default='graph')
    parser.add_argument('--graph-batch',type=int,default=1)
    parser.add_argument('--tokens',type=int,nargs='+',default=[1,2,4,17,128,257,512])
    parser.add_argument('--hidden',type=int,nargs='+',default=[4096,7168])
    args=parser.parse_args()
    if args.graph_batch < 1 or (args.graph_batch > 1 and args.timing != 'graph'):
        parser.error('queued replay batching requires graph mode and a positive batch')
    args.output.mkdir(parents=True,exist_ok=False)
    if args.registration=='production':
        assert enable_custom_op()
    else:
        torch.ops.load_library('/mnt/workspace/hc-pre-reduction-20260930/extension/hc_pre_reduction_probe.so')
    torch.set_num_threads(1)
    torch_npu.npu.config.allow_internal_format=True
    spec=importlib.util.spec_from_file_location('unaltered_benchmark',args.repo/'benchmarks/hc_pre.py')
    benchmark=importlib.util.module_from_spec(spec);spec.loader.exec_module(benchmark)
    runtime_options = {'jit_compile_disabled':torch.npu.is_jit_compile_false(),
                       # torch_npu 2.10 exposes this setting through a write-only
                       # descriptor. Record our explicit request, not a getter
                       # value that this version does not expose.
                       'allow_internal_format_requested':True,
                       'allow_internal_format_effective':None,
                       'allow_matmul_hf32':torch.npu.matmul.allow_hf32,
                       'allow_conv_hf32':torch.npu.conv.allow_hf32,
                       'deterministic_algorithms':torch.are_deterministic_algorithms_enabled()}
    report={'runtime_options':runtime_options,'scope':'Complete HcPre steady queued graph; external event boundaries amortized over graph_batch replays; no model throughput claim',
            'registration':args.registration,'timing':args.timing,'warmup':args.warmup,'samples':args.samples,'rounds':args.rounds,
            'graph_batch':args.graph_batch,'calls_per_sample':20*args.graph_batch if args.timing=='graph' else 1,
            'schema':str(torch.ops._C_ascend.npu_hc_pre_v3.default._schema),'torch':torch.__version__,
            'torch_npu':torch_npu.__version__,'device':torch.npu.get_device_name(0),
            'benchmark_sha256':hashlib.sha256((args.repo/'benchmarks/hc_pre.py').read_bytes()).hexdigest(),
            'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'environment':{key:os.environ.get(key) for key in ('TASK_QUEUE_ENABLE','ASCEND_LAUNCH_BLOCKING','ASCEND_CUSTOM_OPP_PATH','ASCEND_CACHE_PATH','LD_LIBRARY_PATH','OMP_NUM_THREADS','MKL_NUM_THREADS')},
            'cases':[]}
    with torch.inference_mode():
        for hidden in args.hidden:
            for tokens in args.tokens:
                for signed in (False,True):
                    key=f't{tokens}-d{hidden}-signed{int(signed)}'
                    inputs=benchmark.make_inputs(tokens,hidden,signed)
                    input_hashes=[hashlib.sha256(t.cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest() for t in inputs]
                    original=tuple(t.clone() for t in inputs)
                    records=[]
                    for round_index in range(args.rounds):
                        if args.graph_batch == 1:
                            outputs,events,walls=benchmark.measure(inputs,20,args.samples,args.warmup,args.timing,20)
                        else:
                            outputs,events,walls=measure_queued_graph(inputs,args.samples,args.warmup,args.graph_batch)
                        if args.reference:
                            expected=torch.load(args.reference/f'{key}.pt',weights_only=True)
                            for actual,reference in zip(outputs,expected,strict=True):
                                assert torch.equal(actual.view(torch.uint8),reference.view(torch.uint8)),key
                        records.append({'round':round_index,'event_us':events,'wall_us':walls,
                                        'event_median_us':statistics.median(events[args.warmup:]),'wall_median_us':statistics.median(walls[args.warmup:])})
                    for value,reference in zip(inputs,original,strict=True):assert torch.equal(value,reference),key
                    destination=args.output/f'{key}.pt';torch.save(outputs,destination)
                    report['cases'].append({'case':key,'input_sha256':input_hashes,'output_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'bitwise_reference_checked':args.reference is not None,'rounds':records})
                    (args.output/'results.json').write_text(json.dumps(report,indent=2))
                    print(key,[round(r['event_median_us'],3) for r in records],flush=True)
    (args.output/'loaded-libraries.txt').write_text('\n'.join(line for line in Path('/proc/self/maps').read_text().splitlines() if any(s in line for s in ('libcust_','libopapi','probe.so','vllm_ascend_C'))))

if __name__=='__main__':main()
