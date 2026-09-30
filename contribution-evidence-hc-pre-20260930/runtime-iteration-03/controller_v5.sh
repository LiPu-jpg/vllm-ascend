#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-03"
echo "$$" > "$iteration/controller-v5.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v5.exit"' EXIT
for check in $(seq 1 720); do
    if [[ -f "$iteration/controller-v4.exit" ]]; then break; fi
    sleep 5
done
test "$(cat "$iteration/controller-v4.exit")" = 0
grep -q OPTIONAL_PRE_REVERSE_ORDER_CONTROL_COMPLETE "$iteration/controller-v4.log"
for variant in baseline candidate; do
    bash "$iteration/run_model_profile_v5.sh" "$variant" "optional5-model-graph-$variant" model-graph
done
echo OPTIONAL_PRE_ACTUAL_MODEL_GRAPH_TRACE_COMPLETE
