"""Require CPU accuracy and all parity checks for every production/benchmark input."""
import json
from pathlib import Path
import sys
root = Path(sys.argv[1])
for variant in ('baseline', 'candidate'):
    normal = json.loads((root / f'batch-comb2-fixture-{variant}/data/results.json').read_text())
    assert len(normal) == 72
    real = [r for r in normal if r['shape'][-1] in (4096, 7168)]
    assert len(real) == 48
    assert all(r['cpu_accuracy_pass'] and not r['errors'] for r in real), 'Production fixture failure remains'
    benchmark = json.loads((root / f'batch-comb2-benchmark-fixture-{variant}/data/results.json').read_text())
    assert len(benchmark) == 28
    assert all(r['cpu_accuracy_pass'] and not r['errors'] for r in benchmark), 'Benchmark input failure remains'
print('ALL48_PRODUCTION_AND28_BENCHMARK_INPUTS_PASS; SMALL_HIDDEN_FAILURES_REMAIN_RETAINED')
