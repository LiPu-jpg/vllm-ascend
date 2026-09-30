#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-05
echo "$$" > "$iteration/controller-v9.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v9.exit"' EXIT
test "$(cat "$iteration/controller-v7.exit")" = 1
grep -q 'COMPLETED div1-graph-baseline-b' "$iteration/controller-v7.log"
# The old A/A run retains all samples and its failed foreign-after guard.
# New labels collect a separately guarded complete cohort.
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_validation.sh" baseline "div4-graph-aa-$arm" graph div1-graph-baseline-a
done
for arm in candidate-a baseline-a baseline-b candidate-b; do
    variant=${arm%-*}
    bash "$iteration/run_validation.sh" "$variant" "div4-graph-$arm" graph div1-graph-baseline-a
done
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    bash "$iteration/run_validation.sh" "$variant" "div4-event-$arm" event div1-graph-baseline-a
done
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_validation.sh" baseline "div4-event-aa-$arm" event div1-graph-baseline-a
done
echo SHORT_DIV_RECOVERED_ORDER_CONTROLS_COMPLETE
