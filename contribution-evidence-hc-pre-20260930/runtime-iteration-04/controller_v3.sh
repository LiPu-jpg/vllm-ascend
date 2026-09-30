#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-04"
echo "$$" > "$iteration/controller-v3.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v3.exit"' EXIT
for check in $(seq 1 1440); do
    if [[ -f "$iteration/controller-v2.exit" ]]; then break; fi
    sleep 5
done
test "$(cat "$iteration/controller-v2.exit")" = 0
grep -q CONTIGUOUS_CAST_ORDER_CONTROLS_COMPLETE "$iteration/controller-v2.log"
for mode in trace profile-eager profile-graph; do
    for variant in baseline candidate; do
        bash "$iteration/run_validation.sh" "$variant" "cast3-$mode-$variant" "$mode"
    done
done
# Preserve the same isolated prerequisite that prior actual models required.
for variant in baseline candidate; do
    repo="$task_root/cast-source-$variant"
    git -C "$repo" diff > "$iteration/source-before-model-$variant.patch"
    git -C "$repo" apply --check "$task_root/iteration-02/model-prerequisite-17828.patch"
    git -C "$repo" apply "$task_root/iteration-02/model-prerequisite-17828.patch"
    git -C "$repo" diff > "$iteration/source-model-prerequisite-$variant.patch"
done
for mode in model-eager model-graph; do
    for variant in baseline candidate; do
        bash "$iteration/run_validation.sh" "$variant" "cast3-$mode-$variant" "$mode"
    done
done
echo CONTIGUOUS_CAST_PROFILE_MODEL_COMPLETE
