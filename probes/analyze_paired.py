"""Retain all samples and report each case, including every slowdown."""
import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path


def stats(values):
    return dict(median=statistics.median(values), minimum=min(values), maximum=max(values),
                mean=statistics.mean(values), stddev=statistics.stdev(values), samples=values)


parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
args = parser.parse_args()
labels = ['b2', 'c2', 'c3', 'b3', 'b4', 'c4']
runs = {label: json.loads((args.root/f'paired-{label}.json').read_text()) for label in labels}
cases_path = args.root/'probes/sparse_flash_attention_perf_cases.jsonl'
case_hash = hashlib.sha256(cases_path.read_bytes()).hexdigest()
for run in runs.values():
    assert run['complete'] and len(run['rows']) == 52
    assert run['metadata']['cases_sha256'] == case_hash
for key in ('torch_version','torch_npu_version','test_sha256','script_sha256','device'):
    assert len({run['metadata'][key] for run in runs.values()}) == 1, key
cases = [json.loads(x) for x in cases_path.read_text().splitlines()]
summary = []
lines = ['# Nonempty SFA paired performance', '',
         'Run order: B/C/C/B/B/C; three independent processes per variant, five raw samples per case/process.',
         '52 fixed nonempty cases; input hashes, dtype, runtime and scripts match in all runs.',
         'Device: eight native calls captured per graph, ten warmup replays, 100 replays per event pair.',
         'Wall: 25 eager calls plus synchronization per batch. This is amortized wall time, not single-call latency.',
         'Negative delta means lower candidate latency. No significance or model speedup is claimed.', '',
         '| Case | dtype | RoPE | Queries | KV length | Selected/query | Base us [range] | Candidate us [range] | Device delta % | Base wall us | Candidate wall us | Wall delta % |',
         '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
for index, case in enumerate(cases):
    rows = {label: run['rows'][index] for label, run in runs.items()}
    assert len({row['input_sha256'] for row in rows.values()}) == 1
    values = {x['name']: x.get('value', x.get('shape')) for x in case['inputs']}
    row = dict(index=index, dtype=case['inputs'][0]['dtype'], rope_dim=values['rope_dim'],
               query_shape=values['query'], kv_length=values['kv_lengths'][0], selected=values['selected_counts'][0])
    for variant, prefix in [('baseline','b'),('candidate','c')]:
        selected = [rows[label] for label in labels if label.startswith(prefix)]
        row[variant] = dict(device=stats([x for r in selected for x in r['graph_device_us']]),
                            wall=stats([x for r in selected for x in r['eager_batch_wall_us']]),
                            process_device_medians=[statistics.median(r['graph_device_us']) for r in selected],
                            process_wall_medians=[statistics.median(r['eager_batch_wall_us']) for r in selected])
    b, c = row['baseline'], row['candidate']
    row['device_delta_percent'] = (c['device']['median']/b['device']['median']-1)*100
    row['wall_delta_percent'] = (c['wall']['median']/b['wall']['median']-1)*100
    summary.append(row)
    lines.append(f'| {index} | {row["dtype"]} | {row["rope_dim"]} | {row["query_shape"][0]} | {row["kv_length"]} | {row["selected"]} | '
                 f'{b["device"]["median"]:.3f} [{b["device"]["minimum"]:.3f}, {b["device"]["maximum"]:.3f}] | '
                 f'{c["device"]["median"]:.3f} [{c["device"]["minimum"]:.3f}, {c["device"]["maximum"]:.3f}] | '
                 f'{row["device_delta_percent"]:+.2f} | {b["wall"]["median"]:.3f} | {c["wall"]["median"]:.3f} | {row["wall_delta_percent"]:+.2f} |')
faster = [r for r in summary if r['device_delta_percent'] < 0]
slower = [r for r in summary if r['device_delta_percent'] > 0]
lines += ['', f'{len(faster)} lower device medians; {len(slower)} higher device medians.',
          f'Maximum latency reduction: {-min(r["device_delta_percent"] for r in summary):.2f}%.',
          f'Maximum slowdown: {max(r["device_delta_percent"] for r in summary):.2f}%.', '',
          'Raw observations and per-process medians are retained in performance-summary.json and the six paired JSON files.']
(args.root/'performance-table.md').write_text('\n'.join(lines)+'\n')
(args.root/'performance-summary.json').write_text(json.dumps(dict(order=labels,cases_sha256=case_hash,rows=summary),indent=2)+'\n')
with (args.root/'performance-summary.csv').open('w',newline='') as f:
    names=['index','dtype','rope_dim','query_shape','kv_length','selected','device_delta_percent','wall_delta_percent']
    writer=csv.DictWriter(f,fieldnames=names,extrasaction='ignore'); writer.writeheader(); writer.writerows(summary)
print(f'Cases {len(summary)}; lower {len(faster)}, higher {len(slower)}; max loss {max(r["device_delta_percent"] for r in summary):.3f}%')
