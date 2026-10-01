#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-08
echo "$$" > "$iteration/controller-v3c-tail-history.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v3c-tail-history.exit"' EXIT
python3 "$iteration/foreign_jobs.py" > "$iteration/foreign-window-before-tail-history.json"
python3 "$iteration/inspect_terminal_build_products.py" > "$iteration/build-integrity-before-tail-history.json"
python3 "$iteration/verify_shared_validation_dependencies.py" > "$iteration/shared-inputs-before-tail-history.json"
for variant in baseline candidate; do
    label="batch-comb7-state-kernel-selection-$variant"
    bash "$iteration/run_tail_history_validation.sh" "$variant" "$label" trace
    python3 "$iteration/validate_postguards.py" "$iteration/$label"
    python3 "$iteration/verify_kernel_selection.py" \
        "/mnt/workspace/hc-pre-reduction-20260930/batch-comb-source-$variant" \
        "$iteration/full-extension-build-$variant/binary-sha256.json" \
        "$iteration/$label/opened-kernels.json" > "$iteration/$label/verification.log"
    label="batch-comb7-state-$variant"
    set +e
    bash "$iteration/run_tail_history_validation.sh" "$variant" "$label" tail-history
    diagnostic_status=$?
    set -e
    echo "RETAINED_STATUS $label $diagnostic_status"
    test "$diagnostic_status" -le 1
    python3 "$iteration/validate_postguards.py" "$iteration/$label"
done
python3 "$iteration/compare_tail_history_records.py" "$iteration"
echo BATCH_COMB_TAIL_HISTORY_RECORDS_COMPLETE_WITH_FAILURES_RETAINED
