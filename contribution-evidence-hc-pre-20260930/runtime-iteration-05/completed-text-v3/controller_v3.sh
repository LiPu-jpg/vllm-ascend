#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-05"
echo "$$" > "$iteration/controller-v3.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v3.exit"' EXIT
for check in $(seq 1 720); do
    if [[ -f "$iteration/controller-v2.exit" ]]; then break; fi
    sleep 5
done
test "$(cat "$iteration/controller-v2.exit")" = 0
grep -q SHORT_DIV_INITIAL_VALIDATION_COMPLETE "$iteration/controller-v2.log"
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
echo SHORT_DIV_ORDER_CONTROLS_COMPLETE
