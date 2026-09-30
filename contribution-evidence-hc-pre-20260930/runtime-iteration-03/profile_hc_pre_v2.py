"""Profile production HcPre registration without changing model/operator code."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration', choices=('production', 'historical-probe'), default='production')
    parser.add_argument('--mode', choices=('graph', 'eager'), default='graph')
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if args.registration == 'production':
        assert enable_custom_op()
    else:
        # Diagnostic control only: the old probe is not production integration.
        torch.ops.load_library('/mnt/workspace/hc-pre-reduction-20260930/extension/hc_pre_reduction_probe.so')
    torch_npu.npu.config.allow_internal_format = True
    torch.set_num_threads(1)
    if args.registration == 'production':
        spec = importlib.util.spec_from_file_location('production_benchmark', Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-03/hc_pre_v2.py'))
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        make_inputs = benchmark.make_inputs
    else:
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
            return tuple(t.npu() for t in (x, fn, scale, base))
    metadata = {
        'registration': args.registration, 'mode': args.mode,
        'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'schema': str(torch.ops._C_ascend.npu_hc_pre_v2.default._schema),
        'torch': torch.__version__, 'torch_npu': torch_npu.__version__,
        'device': torch.npu.get_device_name(0),
        'environment': {key: os.environ.get(key) for key in (
            'TASK_QUEUE_ENABLE', 'ASCEND_LAUNCH_BLOCKING', 'ASCEND_CUSTOM_OPP_PATH',
            'ASCEND_CACHE_PATH', 'TORCHINDUCTOR_CACHE_DIR', 'LD_LIBRARY_PATH',
            'VLLM_BATCH_INVARIANT', 'PYTORCH_NPU_ALLOC_CONF')},
        'cases': [],
    }
    with torch.inference_mode():
        for tokens, hidden, signed in ((1, 4096, False), (128, 4096, True), (512, 7168, False), (1, 7168, False), (2, 7168, False), (4, 7168, False), (2, 4096, False)):
            key = f't{tokens}-d{hidden}-signed{int(signed)}'
            inputs = make_inputs(tokens, hidden, signed)
            def call():
                return torch.ops._C_ascend.npu_hc_pre_v2(*inputs, 4, 20, 1e-6, 1e-6)
            for _ in range(20):
                expected = call()
            torch.npu.synchronize()
            graph = torch.npu.NPUGraph()
            with torch.npu.graph(graph):
                for _ in range(20):
                    outputs = call()
            for _ in range(20):
                graph.replay()
            torch.npu.synchronize()
            for actual, reference in zip(outputs, expected, strict=True):
                assert torch.equal(actual.view(torch.uint8), reference.view(torch.uint8)), key
            config = torch_npu.profiler._ExperimentalConfig(
                aic_metrics=torch_npu.profiler.AiCMetrics.PipeUtilization,
                profiler_level=torch_npu.profiler.ProfilerLevel.Level1,
                l2_cache=False)
            with torch_npu.profiler.profile(
                activities=[torch_npu.profiler.ProfilerActivity.CPU, torch_npu.profiler.ProfilerActivity.NPU],
                on_trace_ready=torch_npu.profiler.tensorboard_trace_handler(str(args.output / key)),
                schedule=torch_npu.profiler.schedule(wait=0, warmup=1, active=1, repeat=1),
                experimental_config=config, record_shapes=True, with_stack=False, profile_memory=False,
            ) as profiler:
                for step in range(2):
                    for _ in range(3):
                        if args.mode == 'graph':
                            graph.replay()
                        else:
                            for _ in range(20):
                                call()
                    torch.npu.synchronize()
                    profiler.step()
            metadata['cases'].append({'case': key, 'replays': 3, 'calls_per_replay': 20})
            (args.output / 'runtime.json').write_text(json.dumps(metadata, indent=2))
            print('PROFILE_COMPLETE', key, flush=True)
            del graph
    maps = Path('/proc/self/maps').read_text().splitlines()
    (args.output / 'loaded-libraries.txt').write_text('\n'.join(
        line for line in maps if any(name in line for name in ('libcust_', 'libopapi', 'vllm_ascend_C'))) + '\n')


if __name__ == '__main__':
    main()
