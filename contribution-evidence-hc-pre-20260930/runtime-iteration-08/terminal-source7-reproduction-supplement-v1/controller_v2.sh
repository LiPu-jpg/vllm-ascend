#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-08
echo "$$" > "$iteration/controller-v2.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v2.exit"' EXIT
# Inspect completed binaries without changing the retained build/guard status.
python "$iteration/inspect_terminal_build_products.py" > "$iteration/terminal-build-integrity-at-validation.json"
python "$iteration/foreign_jobs.py" > "$iteration/fresh-window-before-recovered-validation.json"
# Verify actual private HcPre object selection before any accuracy result.
# This instrumented process is separate from every later timing process.
for variant in baseline candidate; do
    label="batch-comb0-kernel-selection-$variant"
    bash "$iteration/run_validation.sh" "$variant" "$label" trace
    python "$iteration/validate_postguards.py" "$iteration/$label"
    python "$iteration/verify_kernel_selection.py" \
        "/mnt/workspace/hc-pre-reduction-20260930/batch-comb-source-$variant" \
        "$iteration/full-extension-build-$variant/binary-sha256.json" \
        "$iteration/$label/opened-kernels.json" > "$iteration/$label/verification.log"
done
for mode in nightly fixture benchmark-fixture boundary caller; do
    for variant in baseline candidate; do
        reference=()
        if [[ "$variant" == candidate && "$mode" != nightly ]]; then reference+=("batch-comb1-$mode-baseline"); fi
        label="batch-comb1-$mode-$variant"
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
echo BATCH_COMB_CORRECTNESS_RESULTS_RECORDED_WITH_FAILURES
