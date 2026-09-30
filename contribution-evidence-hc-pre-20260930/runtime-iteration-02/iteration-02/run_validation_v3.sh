#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
iteration="$task_root/iteration-02"
variant=${1:?variant}
label=${2:?unique label}
mode=${3:?mode}
reference=${4:-}
source "$runtime_root/venv/bin/activate"
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/Ascend/nnal/atb/set_env.sh"
source "$task_root/$variant/opp/vendors/reduction_${variant}_transformer/bin/set_env.bash"
result="$iteration/$label"
mkdir "$result"
trap 'status=$?; echo "$status" > "$result/run.exit"' EXIT
repo="$task_root/full-plugin-source-v3"
export PYTHONPATH="$task_root/iteration-01:$iteration:$repo:$runtime_root/vllm:$task_root:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TASK_QUEUE_ENABLE=1 ASCEND_LAUNCH_BLOCKING=0
export ASCEND_CUSTOM_OPP_PATH="$task_root/$variant/opp/vendors/reduction_${variant}_transformer:$runtime_root/vllm-ascend/vllm_ascend/_cann_ops_custom/vendors/custom_transformer"
export ASCEND_CACHE_PATH="$iteration/validation-cache-$variant" TORCHINDUCTOR_CACHE_DIR="$iteration/inductor"
export FULL_RESULT_DIR="$result" FULL_STAGE="$mode"
cd "$repo"
npu-smi info > "$result/npu-before.txt"
grep -q 'No running processes' "$result/npu-before.txt"
python "$task_root/iteration-01/other_busy.py" > "$result/other-jobs.txt"
ps -eo pid,ppid,etimes,%cpu,args > "$result/processes-before.txt"
extra=()
if [[ -n "$reference" ]]; then extra+=(--reference "$iteration/$reference/data"); fi
case "$mode" in
  nightly)
    python "$task_root/full_operator_runner.py" pytest -q tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py --junitxml="$result/tests.xml" > "$result/run.log" 2>&1 ;;
  caller)
    python "$task_root/iteration-01/glm_native_caller.py" --repo "$repo" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  graph|event)
    python "$task_root/full_operator_runner.py" benchmarks/hc_pre.py --label "$label" --output "$result/data" --timing "$mode" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  model-eager|model-graph)
    extra=()
    if [[ "$mode" == model-graph ]]; then extra+=(--graph); fi
    python "$task_root/iteration-01/glm_stock_dummy_smoke.py" --repo "$repo" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  *) exit 2 ;;
esac
npu-smi info > "$result/npu-after.txt"
grep -q 'No running processes' "$result/npu-after.txt"
python "$task_root/iteration-01/other_busy.py" > "$result/other-jobs-after.txt"
printf 'COMPLETED %s\n' "$label"
