#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
iteration="$task_root/iteration-03"
variant=${1:?variant}
label=${2:?unique label}
mode=${3:?mode}
reference=${4:-}
source "$runtime_root/venv/bin/activate"
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/Ascend/nnal/atb/set_env.sh"
source "$task_root/baseline/opp/vendors/reduction_baseline_transformer/bin/set_env.bash"
result="$iteration/$label"
mkdir "$result"
trap 'status=$?; echo "$status" > "$result/run.exit"' EXIT
repo="$task_root/optional-pre-source-$variant"
export PYTHONPATH="$task_root/iteration-01:$iteration:$repo:$runtime_root/vllm:$task_root:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TASK_QUEUE_ENABLE=1 ASCEND_LAUNCH_BLOCKING=0
export ASCEND_CUSTOM_OPP_PATH="$task_root/baseline/opp/vendors/reduction_baseline_transformer:$runtime_root/vllm-ascend/vllm_ascend/_cann_ops_custom/vendors/custom_transformer"
export ASCEND_CACHE_PATH="$iteration/cache-$variant" TORCHINDUCTOR_CACHE_DIR="$iteration/inductor"
export FULL_RESULT_DIR="$result" FULL_STAGE="$mode"
npu-smi info > "$result/npu-before.txt"
grep -q 'No running processes' "$result/npu-before.txt"
python "$task_root/iteration-01/other_busy.py" > "$result/other-jobs.txt"
ps -eo pid,ppid,etimes,%cpu,args > "$result/processes-before.txt"
git -C "$repo" status --short > "$result/source-status.txt"
git -C "$repo" rev-parse HEAD > "$result/source-head.txt"
cd "$repo"
extra=()
if [[ -n "$reference" ]]; then extra+=(--reference "$iteration/$reference/data"); fi
case "$mode" in
  nightly)
    # Collect through the normal repository conftests. The baseline gets only
    # the identical test update; its runtime sources and extension stay intact.
    test_path=tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py
    cp "$test_path" "$result/upstream-test.py"
    cp "$iteration/test_npu_hc_pre.py" "$test_path"
    sha256sum "$test_path" > "$result/test-input-sha256.txt"
    set +e
    python "$task_root/full_operator_runner.py" pytest -q "$test_path" --junitxml="$result/tests.xml" > "$result/run.log" 2>&1
    test_status=$?
    set -e
    cp "$result/upstream-test.py" "$test_path"
    if [[ "$test_status" != 0 ]]; then exit "$test_status"; fi ;;
  graph|event)
    graph_batch=1
    if [[ "$mode" == graph ]]; then graph_batch=32; fi
    python "$task_root/full_operator_runner.py" "$iteration/hc_pre.py" --api v2 --label "$label" --output "$result/data" --timing "$mode" --graph-batch "$graph_batch" --warmup 10 --samples 25 --rounds 3 "${extra[@]}" > "$result/run.log" 2>&1 ;;
  caller)
    python "$task_root/iteration-01/glm_native_caller.py" --repo "$repo" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  model-eager|model-graph)
    extra=()
    if [[ "$mode" == model-graph ]]; then extra+=(--graph); fi
    python "$task_root/iteration-01/glm_stock_dummy_smoke.py" --repo "$repo" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  *) exit 2 ;;
esac
npu-smi info > "$result/npu-after.txt"
grep -q 'No running processes' "$result/npu-after.txt"
python "$task_root/iteration-01/other_busy.py" > "$result/other-jobs-after.txt"
echo "COMPLETED $label"
