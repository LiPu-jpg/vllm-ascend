#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-03"
source /mnt/workspace/mhc-validation-20260930/venv/bin/activate
source /mnt/workspace/mhc-validation-20260930/Ascend/cann/set_env.sh
source /mnt/workspace/mhc-validation-20260930/Ascend/nnal/atb/set_env.sh
trap 'status=$?; echo "$status" > "$iteration/controller-v1.exit"' EXIT
npu-smi info > "$iteration/device-before.txt"
grep -q 'No running processes' "$iteration/device-before.txt"
python "$task_root/iteration-01/other_busy.py" > "$iteration/other-jobs-before.txt"
set +e
bash "$task_root/iteration-02/run_followup_exact3.sh" baseline exact3-boundary-aa2 boundary production exact3-boundary-baseline
boundary_status=$?
set -e
echo "BOUNDARY_AA_STATUS=$boundary_status"
test -f "$task_root/iteration-02/exact3-boundary-aa2/run.log"
npu-smi info > "$iteration/device-after-boundary.txt"
grep -q 'No running processes' "$iteration/device-after-boundary.txt"
python "$task_root/iteration-01/other_busy.py" > "$iteration/other-jobs-after-boundary.txt"
python "$iteration/build_full_extensions.py" > "$iteration/full-builds.log" 2>&1
echo MATCHED_COMPLETE_EXTENSIONS_BUILT
bash "$iteration/run_optional_pre.sh" baseline optional1-nightly-baseline nightly
bash "$iteration/run_optional_pre.sh" candidate optional1-nightly-candidate nightly
for arm in aa-a1 aa-b1 aa-b2 aa-a2; do
    reference=""
    if [[ "$arm" != aa-a1 ]]; then reference=optional1-graph-aa-a1; fi
    bash "$iteration/run_optional_pre.sh" baseline "optional1-graph-$arm" graph "$reference"
done
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    bash "$iteration/run_optional_pre.sh" "$variant" "optional1-graph-$arm" graph optional1-graph-aa-a1
done
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    bash "$iteration/run_optional_pre.sh" "$variant" "optional1-eager-$arm" event optional1-graph-aa-a1
done
echo OPTIONAL_PRE_VALIDATION_CONTROLLER_COMPLETE
