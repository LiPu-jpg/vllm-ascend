#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-03"
echo "$$" > "$iteration/controller-v2.pid"
source /mnt/workspace/mhc-validation-20260930/venv/bin/activate
source /mnt/workspace/mhc-validation-20260930/Ascend/cann/set_env.sh
source /mnt/workspace/mhc-validation-20260930/Ascend/nnal/atb/set_env.sh
trap 'status=$?; echo "$status" > "$iteration/controller-v2.exit"' EXIT
test -f "$iteration/controller-v1.exit"
test -f "$iteration/full-extension-build-candidate/binary-sha256.json"
npu-smi info > "$iteration/device-before-v2.txt"
grep -q 'No running processes' "$iteration/device-before-v2.txt"
python "$task_root/iteration-01/other_busy.py" > "$iteration/other-jobs-before-v2.txt"
bash "$iteration/run_optional_pre_v2.sh" baseline optional2-nightly-baseline nightly
bash "$iteration/run_optional_pre_v2.sh" candidate optional2-nightly-candidate nightly
for variant in baseline candidate; do
    reference=""
    if [[ "$variant" == candidate ]]; then reference=optional2-boundary-baseline; fi
    set +e
    bash "$iteration/run_optional_pre_v2.sh" "$variant" "optional2-boundary-$variant" boundary "$reference"
    status=$?
    set -e
    echo "BOUNDARY $variant status=$status"
    test -f "$iteration/optional2-boundary-$variant/data/results.json"
    npu-smi info > "$iteration/optional2-boundary-$variant/npu-controller-after.txt"
    grep -q 'No running processes' "$iteration/optional2-boundary-$variant/npu-controller-after.txt"
    python "$task_root/iteration-01/other_busy.py" > "$iteration/optional2-boundary-$variant/other-jobs-after.txt"
done
for arm in aa-a1 aa-b1 aa-b2 aa-a2; do
    reference=""
    if [[ "$arm" != aa-a1 ]]; then reference=optional2-graph-aa-a1; fi
    bash "$iteration/run_optional_pre_v2.sh" baseline "optional2-graph-$arm" graph "$reference"
done
for mode in graph event; do
    for arm in baseline-a candidate-a candidate-b baseline-b; do
        variant=${arm%-*}
        bash "$iteration/run_optional_pre_v2.sh" "$variant" "optional2-$mode-$arm" "$mode" optional2-graph-aa-a1
    done
done
echo OPTIONAL_PRE_VALIDATION_CONTROLLER_COMPLETE
