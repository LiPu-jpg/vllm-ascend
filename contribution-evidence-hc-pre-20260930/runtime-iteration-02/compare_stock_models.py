"""Compare actual model results; retain differences before failing a check."""
import hashlib
import json
from pathlib import Path

root = Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-02')
summary = {'scope': 'Four-layer BF16 standard-dummy GLM functional parity, not trained-checkpoint accuracy or model throughput',
           'source': 'd50abbec269b1f55983f122388d608b0fab38a62',
           'shared_prerequisite': 'PR #17828 cbb707903e619db01439e19731b0e688377326fe causal-convolution wrapper only',
           'modes': []}
valid = True
for mode in ('model-eager', 'model-graph'):
    paths = [root / f'exact3-fixed-{variant}-{mode}' / 'data' for variant in ('baseline', 'peeled')]
    files = [path / 'functional-results.json' for path in paths]
    data = [json.loads(path.read_text()) for path in files]
    errors = []
    differences = []
    for baseline, candidate in zip(*data, strict=True):
        if baseline['prompt_length'] != candidate['prompt_length']:
            errors.append('prompt mismatch')
        if baseline['tokens'] != candidate['tokens']:
            errors.append('token mismatch')
        for a, b in zip(baseline['logprobs'], candidate['logprobs'], strict=True):
            if a.keys() != b.keys():
                errors.append('logprob keys mismatch')
            for token in a.keys() & b.keys():
                differences.append(abs(a[token] - b[token]))
    config_hashes = [hashlib.sha256((path / 'model/config.json').read_bytes()).hexdigest() for path in paths]
    if len(set(config_hashes)) != 1:
        errors.append('model fixture mismatch')
    row = {'mode_requested': mode, 'requests': len(data[0]),
           'generated_tokens': sum(len(item['tokens']) for item in data[0]),
           'logprob_values_compared': len(differences), 'max_abs_logprob_difference': max(differences, default=0),
           'errors': errors, 'fixture_sha256': config_hashes,
           'result_files': [{'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in files]}
    summary['modes'].append(row)
    valid &= not errors and row['max_abs_logprob_difference'] == 0
summary['functional_parity_pass'] = valid
(root / 'stock-model-comparison.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
raise SystemExit(not valid)
