"""Profile production HcPre registration without changing model/operator code."""
import argparse
import importlib.util
import json
import os
from pathlib import Path

import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    assert enable_custom_op()
    torch_npu.npu.config.allow_internal_format = True
    torch.set_num_threads(1)
    spec = importlib.util.spec_from_file_location('production_benchmark', args.repo / 'benchmarks/hc_pre.py')
    benchmark = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(benchmark)
    metadata = {
        'schema': str(torch.ops._C_ascend.npu_hc_pre_v3.default._schema),
        'torch': torch.__version__, 'torch_npu': torch_npu.__version__,
        'device': torch.npu.get_device_name(0),
        'environment': {key: os.environ.get(key) for key in (
            'TASK_QUEUE_ENABLE', 'ASCEND_LAUNCH_BLOCKING', 'ASCEND_CUSTOM_OPP_PATH',
            'ASCEND_CACHE_PATH', 'TORCHINDUCTOR_CACHE_DIR', 'LD_LIBRARY_PATH',
            'VLLM_BATCH_INVARIANT', 'PYTORCH_NPU_ALLOC_CONF')},
        'cases': [],
    }
    with torch.inference_mode():
        for tokens, hidden, signed in ((1, 4096, False), (128, 4096, True), (512, 7168, False)):
            key = f't{tokens}-d{hidden}-signed{int(signed)}'
            inputs = benchmark.make_inputs(tokens, hidden, signed)
            def call():
                return torch.ops._C_ascend.npu_hc_pre_v3(
                    *inputs, None, hc_mult=4, hc_sinkhorn_iters=20, norm_eps=1e-6, hc_eps=1e-6)
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
                experimental_config=config, record_shapes=True, with_stack=False, profile_memory=False,
            ) as profiler:
                for _ in range(3):
                    graph.replay()
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
