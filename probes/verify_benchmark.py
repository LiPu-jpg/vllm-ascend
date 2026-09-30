"""Verify the reviewable benchmark reproduces the measured private inputs."""
import importlib.util
import json
from pathlib import Path

from experiment import guard

root = Path('/mnt/workspace/sfa-nonempty-perf-20260930')
spec = importlib.util.spec_from_file_location('benchmark', root/'probes/benchmark_sparse_flash_attention_kv_padding.py')
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)
baseline = json.loads((root/'paired-b2.json').read_text())
assert baseline['complete']
assert benchmark.enable_custom_op()
for index, line in enumerate((root/'probes/sparse_flash_attention_perf_cases.jsonl').read_text().splitlines()):
    guard()
    inputs = benchmark.make_inputs(json.loads(line))
    assert benchmark.input_hash(inputs) == baseline['rows'][index]['input_sha256'], index
    print(f'case {index}: input SHA256 matches measured workload', flush=True)
guard()
