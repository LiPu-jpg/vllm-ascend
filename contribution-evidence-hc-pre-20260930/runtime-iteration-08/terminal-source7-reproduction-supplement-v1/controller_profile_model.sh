#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-08"
echo "$$" > "$iteration/controller-v5-profile-model.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v5-profile-model.exit"' EXIT
test "$(cat "$iteration/controller-v4-performance.exit")" = 0
grep -q BATCH_COMB_ALL28_ORDERED_PERFORMANCE_CONTROLS_COMPLETE "$iteration/controller-v4-performance.log"
for mode in trace profile-eager profile-graph; do
    for variant in baseline candidate; do
        label="batch-comb6-$mode-$variant"
        bash "$iteration/run_validation_hf32_reference.sh" "$variant" "$label" "$mode"
        python "$iteration/validate_postguards.py" "$iteration/$label"
    done
done
# Apply the same isolated model prerequisite only after all operator timings.
# Both unmodified source diffs and the identical prerequisite are retained.
for variant in baseline candidate; do
    repo="$task_root/batch-comb-source-$variant"
    git -C "$repo" diff > "$iteration/source-before-model-$variant.patch"
    test ! -s "$iteration/source-before-model-$variant.patch"
    git -C "$repo" apply --check "$iteration/model-prerequisite-17828.patch"
    git -C "$repo" apply "$iteration/model-prerequisite-17828.patch"
    git -C "$repo" diff > "$iteration/source-model-prerequisite-$variant.patch"
done
cmp "$iteration/source-model-prerequisite-baseline.patch" "$iteration/source-model-prerequisite-candidate.patch"
for mode in model-eager model-graph; do
    for variant in baseline candidate; do
        label="batch-comb6-$mode-$variant"
        bash "$iteration/run_validation_hf32_reference.sh" "$variant" "$label" "$mode"
        python "$iteration/validate_postguards.py" "$iteration/$label"
    done
done
echo BATCH_COMB_PROFILE_MODEL_GUARDED_COMPLETE
