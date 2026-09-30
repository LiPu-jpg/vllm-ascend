"""Summarize every preplanned arm, with CPU-input joins and retained guard status.

The process is the independent experimental unit. Pooled percentiles describe
samples, not confidence intervals. A/A controls are never subtracted as a
correction, and no model throughput is inferred.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

COHORTS = {
    'graph-abba': ('graph', False, ('prefetch1-graph-baseline-a', 'prefetch1-graph-baseline-b'),
                   ('prefetch1-graph-candidate-a', 'prefetch1-graph-candidate-b')),
    'graph-aa': ('graph', True, ('prefetch2-graph-aa-a1', 'prefetch2-graph-aa-a2'),
                 ('prefetch2-graph-aa-b1', 'prefetch2-graph-aa-b2')),
    'graph-baab': ('graph', False, ('prefetch2-graph-baseline-a', 'prefetch2-graph-baseline-b'),
                   ('prefetch2-graph-candidate-a', 'prefetch2-graph-candidate-b')),
    'event-abba': ('event', False, ('prefetch1-event-baseline-a', 'prefetch1-event-baseline-b'),
                   ('prefetch1-event-candidate-a', 'prefetch1-event-candidate-b')),
    'event-aa': ('event', True, ('prefetch2-event-aa-a1', 'prefetch2-event-aa-a2'),
                 ('prefetch2-event-aa-b1', 'prefetch2-event-aa-b2')),
}
EXPECTED_CASES = [f't{t}-d{d}-signed{s}' for d in (4096, 7168)
                  for t in (1, 2, 4, 17, 128, 257, 512) for s in (0, 1)]


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def arm_summary(runs, case_index, metric):
    measured, rounds, processes = [], [], []
    for run in runs:
        process = []
        records = run['cases'][case_index]['rounds']
        assert len(records) == 3
        for record in records:
            raw = record[metric]
            assert len(raw) == run['warmup'] + run['samples']
            samples = raw[run['warmup']:]
            assert all(math.isfinite(v) and v > 0 for v in samples)
            rounds.append(statistics.median(samples))
            process.extend(samples)
        processes.append(statistics.median(process))
        measured.extend(process)
    return {'median_us': statistics.median(measured),
            'p10_us': percentile(measured, .1), 'p90_us': percentile(measured, .9),
            'round_medians_us': rounds, 'process_medians_us': processes,
            'measured_samples': len(measured)}


def metric_summary(runs, metric):
    rows = []
    for i, case in enumerate(EXPECTED_CASES):
        reference = arm_summary(runs[:2], i, metric)
        comparison = arm_summary(runs[2:], i, metric)
        ratio = reference['median_us'] / comparison['median_us']
        rows.append({'case': case, 'reference': reference, 'comparison': comparison,
                     'reference_over_comparison': ratio,
                     'comparison_latency_change_percent': (1 / ratio - 1) * 100,
                     'pair_ratios': [a / b for a, b in zip(reference['process_medians_us'],
                                                         comparison['process_medians_us'], strict=True)]})
    return {'metric': metric, 'cases': rows,
            'geometric_mean_ratio': math.exp(statistics.mean(math.log(r['reference_over_comparison']) for r in rows)),
            'pair_geometric_mean_ratios': [math.exp(statistics.mean(math.log(r['pair_ratios'][i]) for r in rows)) for i in (0, 1)],
            'faster': sum(r['reference_over_comparison'] > 1 for r in rows),
            'slower': sum(r['reference_over_comparison'] < 1 for r in rows),
            'equal': sum(r['reference_over_comparison'] == 1 for r in rows),
            'max_slowdown_percent': max(r['comparison_latency_change_percent'] for r in rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    accuracy = {}
    for variant in ('baseline', 'candidate'):
        cases = json.loads((args.root / f'prefetch1-benchmark-fixture-{variant}/data/results.json').read_text())
        assert [c['case'] for c in cases] == EXPECTED_CASES
        assert all(c['cpu_accuracy_pass'] and not c['errors'] for c in cases)
        accuracy[variant] = {c['case']: c['input_sha256'] for c in cases}
    report = {'scope': 'Complete HcPre operator only; no model throughput claim',
              'statistics': 'Two independent processes per arm; no iid confidence interval or A/A correction',
              'cohorts': {}}
    for label, (timing, control, reference_labels, comparison_labels) in COHORTS.items():
        labels = (*reference_labels, *comparison_labels)
        paths = [args.root / name / 'data/results.json' for name in labels]
        runs = [json.loads(p.read_text()) for p in paths]
        metadata = ('driver_sha256', 'torch', 'torch_npu', 'device', 'api', 'schema',
                    'iterations', 'warmup', 'samples', 'timing', 'calls_per_sample')
        assert all(all(run[k] == runs[0][k] for k in metadata) for run in runs)
        assert runs[0]['timing'] == timing and runs[0]['warmup'] == 10 and runs[0]['samples'] == 25
        assert runs[0]['calls_per_sample'] == (640 if timing == 'graph' else 1)
        assert runs[0]['api'] == 'v2' and runs[0]['iterations'] == 20
        statuses = []
        for name, run in zip(labels, runs, strict=True):
            assert [c['case'] for c in run['cases']] == EXPECTED_CASES
            variant = 'candidate' if 'candidate' in name else 'baseline'
            expected_head = json.loads((args.root / 'revisions.json').read_text())[variant]
            actual_head = (args.root / name / 'source-head.txt').read_text().strip()
            assert actual_head == expected_head
            for case in run['cases']:
                assert case['input_sha256'] == accuracy[variant][case['case']]
                if name != 'prefetch1-graph-baseline-a':
                    assert case['bitwise_reference_checked']
            folder = args.root / name
            guards = json.loads((folder / 'guards-after-status.json').read_text())
            assert set(guards) == {'npu_query', 'npu_idle', 'other_jobs', 'foreign_jobs'}
            statuses.append({'label': name, 'run_exit': (folder / 'run.exit').read_text().strip(),
                             'guards': guards,
                             'foreign_before': json.loads((folder / 'foreign-before.json').read_text()),
                             'foreign_after': json.loads((folder / 'foreign-after.json').read_text()),
                             'device_idle_before': 'No running processes' in (folder / 'npu-before.txt').read_text(),
                             'device_idle_after': 'No running processes' in (folder / 'npu-after.txt').read_text()})
        guarded = all(s['run_exit'] == '0' and all(v == 0 for v in s['guards'].values())
                      and not s['foreign_before'] and not s['foreign_after']
                      and s['device_idle_before'] and s['device_idle_after'] for s in statuses)
        report['cohorts'][label] = {'same_baseline_control': control, 'all_guards_pass': guarded,
                                   'retained_statuses': statuses,
                                   'raw_sources': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
                                   'event': metric_summary(runs, 'event_us'),
                                   'synchronized_host_wall': metric_summary(runs, 'wall_us')}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    assert all(c['all_guards_pass'] for c in report['cohorts'].values()), 'Failed guards retained; not a clean comparison'
    print('All 5 preplanned cohorts, 28 cases each, both timing metrics and all statuses retained')


if __name__ == '__main__':
    main()
