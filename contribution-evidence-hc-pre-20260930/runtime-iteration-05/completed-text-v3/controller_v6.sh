#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-05
echo "$$" > "$iteration/controller-v6.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v6.exit"' EXIT
test "$(cat "$iteration/controller-v5.exit")" = 0
grep -q SHORT_DIV_NIGHTLY_COMPARISON_RECORDED "$iteration/controller-v5.log"
for variant in baseline candidate; do
    extra=()
    if [[ "$variant" == candidate ]]; then extra+=(div1-fixture-baseline); fi
    set +e
    bash "$iteration/run_fixture_diagnostics.sh" "$variant" "div1-fixture-$variant" boundary "${extra[@]}"
    status=$?
    set -e
    echo "FIXTURE_STATUS_$variant=$status"
    test "$status" -le 1
done
python - "$iteration" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
for variant in ('baseline', 'candidate'):
    rows = json.loads((root / f'div1-fixture-{variant}/data/results.json').read_text())
    assert len(rows) == 72
    print('FIXTURE_COUNTS', variant, len(rows), 'CPU_PASS', sum(r['cpu_accuracy_pass'] for r in rows), 'PARITY_FAIL_CASES', sum(bool(r['errors']) for r in rows))
PY
echo SHORT_DIV_FULL_FIXTURE_DIAGNOSTICS_RECORDED
