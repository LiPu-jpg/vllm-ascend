#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-04"
echo "$$" > "$iteration/controller-v2.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v2.exit"' EXIT
for check in $(seq 1 720); do
    if [[ -f "$iteration/controller-v1.exit" ]]; then break; fi
    sleep 5
done
test "$(cat "$iteration/controller-v1.exit")" = 0
grep -q CONTIGUOUS_CAST_INITIAL_VALIDATION_COMPLETE "$iteration/controller-v1.log"
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_validation.sh" baseline "cast2-graph-aa-$arm" graph cast1-graph-baseline-a
done
for arm in candidate-a baseline-a baseline-b candidate-b; do
    variant=${arm%-*}
    bash "$iteration/run_validation.sh" "$variant" "cast2-graph-$arm" graph cast1-graph-baseline-a
done
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    bash "$iteration/run_validation.sh" "$variant" "cast2-event-$arm" event cast1-graph-baseline-a
done
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_validation.sh" baseline "cast2-event-aa-$arm" event cast1-graph-baseline-a
done
echo CONTIGUOUS_CAST_ORDER_CONTROLS_COMPLETE
