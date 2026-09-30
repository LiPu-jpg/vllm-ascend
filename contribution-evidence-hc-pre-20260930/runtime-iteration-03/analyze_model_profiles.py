"""Verify actual graph replay and compare functional outputs in both full models."""
import argparse
import collections
import csv
import hashlib
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = {'scope': 'Standard dummy GLM functional and graph-execution proof; no trained-checkpoint accuracy or model throughput claim',
              'profiles': []}
    outputs = []
    for variant in ('baseline', 'candidate'):
        folder = args.root / f'optional5-model-graph-{variant}'
        assert (folder / 'run.exit').read_text().strip() == '0'
        trace_path, = folder.rglob('trace_view.json')
        data = json.loads(trace_path.read_text())
        events = data['traceEvents'] if isinstance(data, dict) else data
        names = collections.Counter(event.get('name', '') for event in events)
        replay = {key: value for key, value in names.items()
                  if any(term.lower() in key.lower() for term in ('executeasync', 'modelExecute', 'replay', 'aclmdlRI'))}
        with trace_path.with_name('kernel_details.csv').open() as stream:
            kernels = list(csv.DictReader(stream))
        hc = [row for row in kernels if row['Name'] == 'HcPre']
        kernel_names = collections.Counter(row['Name'] for row in kernels)
        result['profiles'].append({
            'variant': variant, 'trace_sha256': hashlib.sha256(trace_path.read_bytes()).hexdigest(),
            'replay_events': replay, 'HcPre_count': len(hc),
            'HcPre_model_ids': dict(collections.Counter(row['Model ID'] for row in hc)),
            'kernel_names': dict(kernel_names),
            'model_config_sha256': hashlib.sha256((folder / 'data/model/config.json').read_bytes()).hexdigest(),
        })
        outputs.append(json.loads((folder / 'data/functional-results.json').read_text()))
    differences = []
    errors = []
    for a, b in zip(*outputs, strict=True):
        if (a['profiled'], a['prompt_length'], a['tokens']) != (b['profiled'], b['prompt_length'], b['tokens']):
            errors.append('request or token mismatch')
        for x, y in zip(a['logprobs'], b['logprobs'], strict=True):
            if x.keys() != y.keys():
                errors.append('logprob key mismatch')
            for key in x.keys() & y.keys():
                if not math.isfinite(x[key]) or not math.isfinite(y[key]):
                    errors.append('nonfinite logprob')
                differences.append(abs(x[key] - y[key]))
    if len({row['model_config_sha256'] for row in result['profiles']}) != 1:
        errors.append('different model fixtures')
    result['functional_comparison'] = {'requests_per_arm': len(outputs[0]),
                                      'tokens_per_arm': sum(len(item['tokens']) for item in outputs[0]),
                                      'logprob_values_compared': len(differences),
                                      'max_abs_logprob_difference': max(differences, default=0),
                                      'errors': errors}
    result['functional_parity_pass'] = not errors and max(differences, default=0) == 0
    args.output.write_text(json.dumps(result, indent=2))
    for row in result['profiles']:
        print(row['variant'], row['replay_events'], row['HcPre_count'], row['HcPre_model_ids'])
    print(result['functional_comparison'])
    assert result['functional_parity_pass']


if __name__ == '__main__':
    main()
