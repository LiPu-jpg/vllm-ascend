#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-07
echo "$$" > "$iteration/controller-v3.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v3.exit"' EXIT
test "$(cat "$iteration/controller-v2.exit")" = 0
grep -q PREFETCH_X_CORRECTNESS_RESULTS_RECORDED_WITH_FAILURES "$iteration/controller-v2.log"
python "$iteration/validate_comparison_inputs.py" "$iteration"
# Each timed arm is a new process. Every fixture/sample is kept.
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    reference=()
    if [[ "$arm" != baseline-a ]]; then reference+=(prefetch1-graph-baseline-a); fi
    bash "$iteration/run_validation.sh" "$variant" "prefetch1-graph-$arm" graph "${reference[@]}"
    python "$iteration/validate_postguards.py" "$iteration/prefetch1-graph-$arm"
done
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_validation.sh" baseline "prefetch2-graph-aa-$arm" graph prefetch1-graph-baseline-a
    python "$iteration/validate_postguards.py" "$iteration/prefetch2-graph-aa-$arm"
done
for arm in candidate-a baseline-a baseline-b candidate-b; do
    variant=${arm%-*}
    bash "$iteration/run_validation.sh" "$variant" "prefetch2-graph-$arm" graph prefetch1-graph-baseline-a
    python "$iteration/validate_postguards.py" "$iteration/prefetch2-graph-$arm"
done
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    bash "$iteration/run_validation.sh" "$variant" "prefetch1-event-$arm" event prefetch1-graph-baseline-a
    python "$iteration/validate_postguards.py" "$iteration/prefetch1-event-$arm"
done
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_validation.sh" baseline "prefetch2-event-aa-$arm" event prefetch1-graph-baseline-a
    python "$iteration/validate_postguards.py" "$iteration/prefetch2-event-aa-$arm"
done
echo PREFETCH_X_ALL28_ORDERED_PERFORMANCE_CONTROLS_COMPLETE
