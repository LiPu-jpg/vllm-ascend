#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-05"
echo "$$" > "$iteration/controller-v10.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v10.exit"' EXIT
test "$(cat "$iteration/controller-v9.exit")" = 0
grep -q SHORT_DIV_RECOVERED_ORDER_CONTROLS_COMPLETE "$iteration/controller-v9.log"
for mode in trace profile-eager profile-graph; do
    for variant in baseline candidate; do
        bash "$iteration/run_validation.sh" "$variant" "div3-$mode-$variant" "$mode"
    done
done
# Preserve the same isolated prerequisite that prior actual models required.
for variant in baseline candidate; do
    repo="$task_root/short-div-source-$variant"
    git -C "$repo" diff > "$iteration/source-before-model-$variant.patch"
    git -C "$repo" apply --check "$task_root/iteration-02/model-prerequisite-17828.patch"
    git -C "$repo" apply "$task_root/iteration-02/model-prerequisite-17828.patch"
    git -C "$repo" diff > "$iteration/source-model-prerequisite-$variant.patch"
done
for mode in model-eager model-graph; do
    for variant in baseline candidate; do
        bash "$iteration/run_validation.sh" "$variant" "div3-$mode-$variant" "$mode"
    done
done
echo SHORT_DIV_PROFILE_MODEL_WITH_RETAINED_FAILURES_COMPLETE
