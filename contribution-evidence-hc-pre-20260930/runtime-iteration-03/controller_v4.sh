#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-03"
echo "$$" > "$iteration/controller-v4.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v4.exit"' EXIT
for check in $(seq 1 720); do
    if [[ -f "$iteration/controller-v3.exit" ]]; then break; fi
    sleep 5
done
test "$(cat "$iteration/controller-v3.exit")" = 0
grep -q OPTIONAL_PRE_CALLER_PROFILE_MODEL_CONTROLLER_COMPLETE "$iteration/controller-v3.log"
for arm in aa-a1 aa-b1 aa-b2 aa-a2; do
    bash "$iteration/run_optional_pre_v2.sh" baseline "optional4-event-$arm" event optional2-graph-aa-a1
done
# Reverse the comparison order to expose drift rather than selecting the first ABBA.
for arm in candidate-a baseline-a baseline-b candidate-b; do
    variant=${arm%-*}
    bash "$iteration/run_optional_pre_v2.sh" "$variant" "optional4-graph-$arm" graph optional2-graph-aa-a1
done
echo OPTIONAL_PRE_REVERSE_ORDER_CONTROL_COMPLETE
