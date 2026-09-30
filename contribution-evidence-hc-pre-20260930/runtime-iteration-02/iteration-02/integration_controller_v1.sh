#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-02"
runtime_root=/mnt/workspace/mhc-validation-20260930
trap 'status=$?; echo "$status" > "$iteration/integration-controller-v1.exit"' EXIT
for check in $(seq 1 720); do
    if [[ -f "$iteration/idle-controls-v2.exit" ]]; then break; fi
    sleep 5
done
test -f "$iteration/idle-controls-v2.exit"
source "$runtime_root/venv/bin/activate"
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/Ascend/nnal/atb/set_env.sh"
idle() {
    npu-smi info > "$iteration/integration-idle-latest.txt"
    grep -q 'No running processes' "$iteration/integration-idle-latest.txt"
    python "$task_root/iteration-01/other_busy.py"
}
idle
python "$iteration/build_full_extension_v3.py" > "$iteration/full-extension-build-v3.log" 2>&1
idle
bash "$iteration/run_validation_v3.sh" peeled exact3-peeled-nightly nightly
# Keep all unmodified-head failures. A failed smoke does not invalidate its
# exit/log evidence or authorize masking the failure with changed model weights.
set +e
bash "$iteration/run_validation_v3.sh" baseline exact3-unpatched-model-eager model-eager
echo "UNPATCHED_MODEL_EXIT $?"
set -e
idle
git -C "$task_root/full-plugin-source-v3" apply --check "$iteration/model-prerequisite-17828.patch"
git -C "$task_root/full-plugin-source-v3" apply "$iteration/model-prerequisite-17828.patch"
git -C "$task_root/full-plugin-source-v3" diff > "$iteration/exact3-model-prerequisite.diff"
for mode in model-eager model-graph; do
    for variant in baseline peeled; do
        idle
        bash "$iteration/run_validation_v3.sh" "$variant" "exact3-fixed-$variant-$mode" "$mode"
    done
done
echo SOURCE_EXACT_INTEGRATION_COMPLETE
