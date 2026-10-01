#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-08
echo "$$" > "$iteration/controller-v4-performance.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v4-performance.exit"' EXIT
test "$(cat "$iteration/controller-v3-hf32-reference.exit")" = 0
grep -q BATCH_COMB_CORRECTED_HF32_REFERENCE_RESULTS_RECORDED_WITH_FAILURES "$iteration/controller-v3-hf32-reference.log"
python "$iteration/validate_comparison_inputs_hf32.py" "$iteration"
# Each timed arm is a new process. Every fixture/sample is kept.
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    reference=()
    if [[ "$arm" != baseline-a ]]; then reference+=(batch-comb4-graph-baseline-a); fi
    bash "$iteration/run_performance.sh" "$variant" "batch-comb4-graph-$arm" graph "${reference[@]}"
    python "$iteration/validate_postguards.py" "$iteration/batch-comb4-graph-$arm"
done
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_performance.sh" baseline "batch-comb5-graph-aa-$arm" graph batch-comb4-graph-baseline-a
    python "$iteration/validate_postguards.py" "$iteration/batch-comb5-graph-aa-$arm"
done
for arm in candidate-a baseline-a baseline-b candidate-b; do
    variant=${arm%-*}
    bash "$iteration/run_performance.sh" "$variant" "batch-comb5-graph-$arm" graph batch-comb4-graph-baseline-a
    python "$iteration/validate_postguards.py" "$iteration/batch-comb5-graph-$arm"
done
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    bash "$iteration/run_performance.sh" "$variant" "batch-comb4-event-$arm" event batch-comb4-graph-baseline-a
    python "$iteration/validate_postguards.py" "$iteration/batch-comb4-event-$arm"
done
for arm in a1 b1 b2 a2; do
    bash "$iteration/run_performance.sh" baseline "batch-comb5-event-aa-$arm" event batch-comb4-graph-baseline-a
    python "$iteration/validate_postguards.py" "$iteration/batch-comb5-event-aa-$arm"
done
echo BATCH_COMB_ALL28_ORDERED_PERFORMANCE_CONTROLS_COMPLETE
