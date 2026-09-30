#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-07
echo "$$" > "$iteration/controller-v2.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v2.exit"' EXIT
test "$(cat "$iteration/controller-v1.exit")" = 0
grep -q PREFETCH_X_MATCHED_BUILDS_COMPLETE "$iteration/controller-v1.log"
for mode in nightly fixture benchmark-fixture boundary caller; do
    for variant in baseline candidate; do
        reference=()
        if [[ "$variant" == candidate && "$mode" != nightly ]]; then reference+=("prefetch1-$mode-baseline"); fi
        label="prefetch1-$mode-$variant"
        set +e
        bash "$iteration/run_validation.sh" "$variant" "$label" "$mode" "${reference[@]}"
        validation_status=$?
        set -e
        echo "RETAINED_STATUS $label $validation_status"
        python "$iteration/validate_postguards.py" "$iteration/$label"
        if [[ "$mode" == caller ]]; then test "$validation_status" = 0; else test "$validation_status" -le 1; fi
    done
    if [[ "$mode" == nightly ]]; then python "$iteration/compare_nightly.py" "$iteration"; fi
done
echo PREFETCH_X_CORRECTNESS_RESULTS_RECORDED_WITH_FAILURES
