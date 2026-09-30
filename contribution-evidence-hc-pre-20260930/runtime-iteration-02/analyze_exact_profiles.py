"""Summarize every completed operator profile and actual model graph trace."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import statistics


def main():
    root = Path(__file__).parent / 'completed-diagnostics-v2'
    rows = []
    fields = ('Duration(us)', 'aicore_time(us)', 'aic_scalar_time(us)',
              'aiv_time(us)', 'aiv_scalar_time(us)', 'aiv_mte3_time(us)', 'aiv_vec_time(us)')
    for path in sorted((root / 'iteration-01').rglob('kernel_details.csv')):
        items = [row for row in csv.DictReader(path.open()) if row['Name'] == 'HcPre']
        assert len(items) == 60, path
        relative = path.relative_to(root)
        row = {'experiment': relative.parts[1], 'case': relative.parts[3],
               'count': len(items), 'source': str(relative),
               'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        for field in fields:
            vals = [float(item[field]) for item in items if item.get(field) not in (None, '', 'N/A')]
            row[field] = statistics.median(vals) if vals else None
        rows.append(row)
    assert len(rows) == 42
    models = []
    for path in sorted((root / 'iteration-02').rglob('trace_view.json')):
        data = json.loads(path.read_text())
        events = data.get('traceEvents', data) if isinstance(data, dict) else data
        names = collections.Counter(event.get('name', '') for event in events)
        replay = {key: value for key, value in names.items()
                  if any(term.lower() in key.lower() for term in ('executeasync', 'modelExecute', 'replay', 'aclmdlRI'))}
        kernels = list(csv.DictReader(path.with_name('kernel_details.csv').open()))
        hc = [row for row in kernels if row['Name'] == 'HcPre']
        models.append({'source': str(path.relative_to(root)),
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'replay_events': replay, 'HcPre_count': len(hc),
                       'HcPre_model_ids': dict(collections.Counter(row['Model ID'] for row in hc)),
                       'kernel_names': dict(collections.Counter(row['Name'] for row in kernels))})
    result = {'scope': 'L1 profiling diagnostics; profiled durations are not performance benchmark samples',
              'operator_profiles': rows, 'model_traces': models}
    (Path(__file__).parent / 'exact3-profile-summary.json').write_text(json.dumps(result, indent=2))
    index = {(row['experiment'], row['case']): row for row in rows}
    cases = sorted({row['case'] for row in rows})
    for mode in ('eager', 'probe'):
        for case in cases:
            variants = [index[(f'exact3-profile-{variant}-{mode}', case)] for variant in ('baseline', 'candidate', 'peeled')]
            print(mode, case, 'total', [row['Duration(us)'] for row in variants],
                  'aiv_scalar', [row['aiv_scalar_time(us)'] for row in variants])
    print('MODELS', models)


if __name__ == '__main__':
    main()
