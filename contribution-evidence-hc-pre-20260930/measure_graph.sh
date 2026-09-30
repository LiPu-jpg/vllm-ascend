#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
source /mnt/workspace/mhc-validation-20260930/Ascend/cann/set_env.sh
trap 'status=$?; echo "$status" > "$task_root/graph-validation.exit"' EXIT
for step in baseline-a candidate-a candidate-b baseline-b; do
    for attempt in $(seq 1 60); do
        npu-smi info > "$task_root/graph-idle-check.txt"
        if grep -q 'No running processes' "$task_root/graph-idle-check.txt"; then break; fi
        sleep 10
    done
    grep -q 'No running processes' "$task_root/graph-idle-check.txt"
    reference=graph-baseline-a
    if [[ "$step" == baseline-a ]]; then reference=baseline-a; fi
    bash "$task_root/run_variant.sh" "${step%-*}" benchmark "graph-$step" "$reference" graph
done
