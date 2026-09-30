#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-05
echo "$$" > "$iteration/controller-v5.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v5.exit"' EXIT
# Reuse the two successful builds. The failed baseline run is retained.
test "$(cat "$iteration/controller-v2.exit")" = 1
set +e
bash "$iteration/run_validation.sh" candidate div1-nightly-candidate nightly
candidate_status=$?
set -e
echo "CANDIDATE_NIGHTLY_STATUS=$candidate_status"
test "$candidate_status" -le 1
python - "$iteration" <<'PY'
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
root = Path(sys.argv[1])
rows = {}
for variant in ('baseline', 'candidate'):
    cases = ET.parse(root / f'div1-nightly-{variant}/tests.xml').findall('.//testcase')
    assert len(cases) == 77
    rows[variant] = [{'case': c.attrib['name'], 'failure': c.find('failure').attrib.get('message') if c.find('failure') is not None else None, 'error': c.find('error').attrib.get('message') if c.find('error') is not None else None} for c in cases]
(root / 'nightly-comparison.json').write_text(json.dumps(rows, indent=2))
for variant, cases in rows.items():
    print('NIGHTLY', variant, 'total', len(cases), 'failed', sum(bool(c['failure'] or c['error']) for c in cases))
print('FAILURE_BITMAP_EQUAL', [r['case'] for r in rows['baseline'] if r['failure'] or r['error']] == [r['case'] for r in rows['candidate'] if r['failure'] or r['error']])
PY
echo SHORT_DIV_NIGHTLY_COMPARISON_RECORDED
