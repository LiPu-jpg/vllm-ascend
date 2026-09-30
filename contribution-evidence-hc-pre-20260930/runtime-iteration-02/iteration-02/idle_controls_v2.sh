#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-02
trap 'status=$?; echo "$status" > "$iteration/idle-controls-v2.exit"' EXIT
run() {
    echo "START $*"
    bash "$iteration/run_followup.sh" "$@"
    echo "RESULT $2 status=0"
    source /mnt/workspace/mhc-validation-20260930/Ascend/cann/set_env.sh
    npu-smi info > "$iteration/$2/npu-controller-after.txt"
    grep -q 'No running processes' "$iteration/$2/npu-controller-after.txt"
    python3 /mnt/workspace/hc-pre-reduction-20260930/iteration-01/other_busy.py > "$iteration/$2/other-jobs-after.txt"
}
# Three successful binary-open traces are retained from idle1. This retry fixes
# only the write-only configuration getter used by the timing metadata.
for arm in a1 b1 b2 a2; do
    reference=""
    if [[ "$arm" != a1 ]]; then reference=idle2-aa-a1; fi
    run baseline "idle2-aa-$arm" registration production "$reference" 500
done
for arm in baseline-a peeled-a peeled-b baseline-b; do
    variant=${arm%-*}
    run "$variant" "idle2-$arm" registration production idle2-aa-a1 500
done
echo IDLE_CONTROLS_COMPLETE
