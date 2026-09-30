#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-03"
echo "$$" > "$iteration/controller-v3.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v3.exit"' EXIT
for check in $(seq 1 720); do
    if [[ -f "$iteration/controller-v2.exit" ]]; then break; fi
    sleep 5
done
test "$(cat "$iteration/controller-v2.exit")" = 0
grep -q OPTIONAL_PRE_VALIDATION_CONTROLLER_COMPLETE "$iteration/controller-v2.log"
bash "$iteration/run_optional_pre_v3.sh" baseline optional3-caller-baseline caller
bash "$iteration/run_optional_pre_v3.sh" candidate optional3-caller-candidate caller optional3-caller-baseline
for mode in profile-eager profile-graph trace; do
    for variant in baseline candidate; do
        bash "$iteration/run_optional_pre_v3.sh" "$variant" "optional3-$mode-$variant" "$mode"
    done
done
set +e
bash "$iteration/run_optional_pre_v3.sh" baseline optional3-model-unpatched-baseline model-eager
status=$?
set -e
echo "UNPATCHED_MODEL_STATUS=$status"
test -f "$iteration/optional3-model-unpatched-baseline/run.log"
# Preserve the unpatched result and record the identical independent dependency.
for variant in baseline candidate; do
    repo="$task_root/optional-pre-source-$variant"
    git -C "$repo" diff > "$iteration/source-before-model-$variant.patch"
    git -C "$repo" apply --check "$task_root/iteration-02/model-prerequisite-17828.patch"
    git -C "$repo" apply "$task_root/iteration-02/model-prerequisite-17828.patch"
    git -C "$repo" diff > "$iteration/source-model-prerequisite-$variant.patch"
done
for mode in model-eager model-graph; do
    for variant in baseline candidate; do
        bash "$iteration/run_optional_pre_v3.sh" "$variant" "optional3-$mode-$variant" "$mode"
    done
done
echo OPTIONAL_PRE_CALLER_PROFILE_MODEL_CONTROLLER_COMPLETE
