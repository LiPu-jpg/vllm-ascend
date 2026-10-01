#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-08
echo "$$" > "$iteration/controller-v3b-generic.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v3b-generic.exit"' EXIT
test "$(cat "$iteration/controller-v3-hf32-reference.exit")" = 0
python3 "$iteration/verify_shared_validation_dependencies.py" > "$iteration/shared-inputs-before-generic.json"
python3 "$iteration/foreign_jobs.py" > "$iteration/foreign-window-before-generic.json"
for variant in baseline candidate; do
    reference=()
    if [[ "$variant" == candidate ]]; then reference+=("batch-comb3-generic-baseline"); fi
    label="batch-comb3-generic-$variant"
    set +e
    bash "$iteration/run_generic_comb_validation.sh" "$variant" "$label" generic "${reference[@]}"
    validation_status=$?
    set -e
    echo "RETAINED_STATUS $label $validation_status"
    test "$validation_status" -le 1
    python3 "$iteration/validate_postguards.py" "$iteration/$label"
done
python3 "$iteration/compare_generic_validation.py" "$iteration"
echo BATCH_COMB_GENERIC_WIDTH_RESULTS_RECORDED_WITH_FAILURES
