"""Record every case and require matching failures before further comparison."""
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
root = Path(sys.argv[1])
rows = {}
for variant in ('baseline', 'candidate'):
    cases = ET.parse(root / f'batch-comb2-nightly-{variant}/tests.xml').findall('.//testcase')
    assert len(cases) == 99, len(cases)
    rows[variant] = [{
        'case': c.attrib['name'],
        'failure': c.find('failure').attrib.get('message') if c.find('failure') is not None else None,
        'error': c.find('error').attrib.get('message') if c.find('error') is not None else None,
        'skipped': c.find('skipped') is not None,
    } for c in cases]
(root / 'nightly-hf32-reference-comparison.json').write_text(json.dumps(rows, indent=2))
failed = lambda entries: [r['case'] for r in entries if r['failure'] or r['error'] or r['skipped']]
for variant, entries in rows.items():
    print('NIGHTLY', variant, len(entries), 'FAILED', len(failed(entries)), flush=True)
assert [r['case'] for r in rows['baseline']] == [r['case'] for r in rows['candidate']]
assert failed(rows['baseline']) == failed(rows['candidate']), 'Candidate failure set differs'
for entries in rows.values():
    assert not any(r['case'].startswith(('test_npu_hc_pre_graph_reads_updated_x', 'test_npu_hc_pre_graph_reads_updated_external_pre_mix')) and (r['failure'] or r['error'] or r['skipped']) for r in entries)
    midpoint = [r for r in entries if r['case'].startswith('test_npu_hc_pre_hf32_midpoint_rounding')]
    assert len(midpoint) == 6, len(midpoint)
    assert not failed(midpoint), 'New HF32 hardware regressions must pass independently'
print('ALL6_HF32_MIDPOINT_HARDWARE_REGRESSIONS_PASS_PER_ARM')
print('FAILURE_BITMAP_EQUAL; FAILURES_RETAINED_NOT_PASSED')
