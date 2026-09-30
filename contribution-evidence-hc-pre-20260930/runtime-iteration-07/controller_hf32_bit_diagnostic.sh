#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-07
echo "$$" > "$iteration/controller-hf32-bit.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-hf32-bit.exit"' EXIT
test "$(cat "$iteration/controller-v2.exit")" = 0
python3 "$iteration/foreign_jobs.py" > "$iteration/foreign-before-hf32-bit.json"
label=prefetch-diagnostic-hf32-bits-baseline
bash "$iteration/run_hf32_bit_diagnostic.sh" baseline "$label" trace
python3 "$iteration/validate_postguards.py" "$iteration/$label"
python3 "$iteration/verify_kernel_selection.py" \
    /mnt/workspace/hc-pre-reduction-20260930/prefetch-x-source-baseline \
    "$iteration/full-extension-build-baseline/binary-sha256.json" \
    "$iteration/$label/opened-kernels.json" > "$iteration/$label/verification.log"
echo CONTROLLED_PRODUCTION_HF32_BITS_GUARDED_COMPLETE
