#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-05
echo "$$" > "$iteration/controller-v7.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v7.exit"' EXIT
test "$(cat "$iteration/controller-v6.exit")" = 0
grep -q SHORT_DIV_FULL_FIXTURE_DIAGNOSTICS_RECORDED "$iteration/controller-v6.log"
for variant in baseline candidate; do
    extra=()
    if [[ "$variant" == candidate ]]; then extra+=(div1-boundary-baseline); fi
    set +e
    bash "$iteration/run_validation.sh" "$variant" "div1-boundary-$variant" boundary "${extra[@]}"
    status=$?
    set -e
    echo "BOUNDARY_STATUS_$variant=$status"
    test "$status" -le 1
done
python - "$iteration" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
for variant in ('baseline', 'candidate'):
    rows = json.loads((root / f'div1-boundary-{variant}/data/results.json').read_text())
    assert len(rows) == 60
    print('RETAINED_BOUNDARY', variant, len(rows), 'cpu_pass', sum(r['cpu_accuracy_pass'] for r in rows), 'parity_fail_cases', sum(bool(r['errors']) for r in rows))
PY
bash "$iteration/run_validation.sh" baseline div1-caller-baseline caller
bash "$iteration/run_validation.sh" candidate div1-caller-candidate caller div1-caller-baseline
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    extra=()
    if [[ "$arm" != baseline-a ]]; then extra+=(div1-graph-baseline-a); fi
    bash "$iteration/run_validation.sh" "$variant" "div1-graph-$arm" graph "${extra[@]}"
done
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_validation.sh" baseline "div2-graph-aa-$arm" graph div1-graph-baseline-a
done
for arm in candidate-a baseline-a baseline-b candidate-b; do
    variant=${arm%-*}
    bash "$iteration/run_validation.sh" "$variant" "div2-graph-$arm" graph div1-graph-baseline-a
done
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    bash "$iteration/run_validation.sh" "$variant" "div2-event-$arm" event div1-graph-baseline-a
done
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_validation.sh" baseline "div2-event-aa-$arm" event div1-graph-baseline-a
done
echo SHORT_DIV_ORDER_CONTROLS_WITH_RETAINED_FAILURES_COMPLETE
