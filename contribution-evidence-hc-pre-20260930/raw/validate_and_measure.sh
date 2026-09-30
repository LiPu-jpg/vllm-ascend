#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
source /mnt/workspace/mhc-validation-20260930/Ascend/cann/set_env.sh
trap 'status=$?; echo "$status" > "$task_root/validation.exit"' EXIT
test "$(cat "$task_root/build.exit")" = 0
wait_idle() {
    for attempt in $(seq 1 60); do
        npu-smi info > "$task_root/idle-check.txt"
        if grep -q 'No running processes' "$task_root/idle-check.txt"; then return; fi
        sleep 10
    done
    echo 'Device remained busy; no process was stopped.' >&2
    return 42
}
wait_idle
bash "$task_root/run_variant.sh" baseline test baseline-tests-v3
wait_idle
bash "$task_root/run_variant.sh" candidate test candidate-tests-v3
for step in baseline-a candidate-a candidate-b baseline-b; do
    wait_idle
    variant=${step%-*}
    reference=baseline-a
    if [[ "$step" == baseline-a ]]; then reference=; fi
    bash "$task_root/run_variant.sh" "$variant" benchmark "$step" "$reference"
done
