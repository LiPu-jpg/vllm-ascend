"""Classify independent rounding controls without changing the test oracle."""
import argparse
import hashlib
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--iteration', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.iteration
assert (root / 'controller-hf32-rounding.exit').read_text().strip() == '0'
phase = root / 'prefetch-diagnostic-hf32-roundings-baseline'
guards = json.loads((phase / 'guards-after-status.json').read_text())
assert guards == {'npu_query': 0, 'npu_idle': 0, 'other_jobs': 0, 'foreign_jobs': 0}
assert json.loads((phase / 'foreign-before.json').read_text()) == []
assert json.loads((phase / 'foreign-after.json').read_text()) == []
assert (phase / 'run.exit').read_text().strip() == '0'
selected = json.loads((phase / 'opened-kernels.json').read_text())
assert any(row['sha256'] == 'e4fe3ba278578281a0bb142d5da21cbfeb6d55e355378112fc429440eea23622'
           for row in selected)
raw = phase / 'data/results.json'
rows = json.loads(raw.read_text())
expected_keys = {f'd{d}-{anchor}-{offset}' for d in (4096, 7168)
                 for anchor in ('even', 'odd', 'exponent-carry')
                 for offset in ('zero', 'quarter', 'below-half', 'half', 'above-half', 'three-quarter', 'next-grid')}
assert len(rows) == 42 and {row['case'] for row in rows} == expected_keys
assert all(row['all_outputs_finite'] for row in rows)
models = {}
for model in rows[0]['references']:
    errors = [row['references'][model]['max_abs_difference'] for row in rows]
    assert all(math.isfinite(value) for value in errors)
    models[model] = {'max_abs_difference': max(errors),
                     'aligned_cases_at_2e_minus6': sum(value <= 2e-6 for value in errors),
                     'misaligned_cases': [row['case'] for row, value in zip(rows, errors, strict=True) if value > 2e-6]}
all_aligned = [model for model, stats in models.items() if stats['aligned_cases_at_2e_minus6'] == 42]
conclusion = {'scope': 'Controlled normal FP32 coefficients on the verified 910B3 production baseline; no special-value or other-architecture certification',
              'raw_results_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
              'analyzer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'cases': 42, 'models': models, 'all_aligned_models': all_aligned,
              'threshold_scope': '2e-6 is diagnostic model alignment only; nightly and benchmark accuracy thresholds are unchanged',
              'original_oracle_changed': False, 'performance_started': False}
assert not args.output.exists()
args.output.write_text(json.dumps(conclusion, indent=2) + '\n')
print(json.dumps(conclusion), flush=True)
