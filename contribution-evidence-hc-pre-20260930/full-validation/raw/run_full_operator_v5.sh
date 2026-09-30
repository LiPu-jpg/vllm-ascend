#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/venv/bin/activate"
source "$task_root/baseline/opp/vendors/reduction_baseline_transformer/bin/set_env.bash"
result="$task_root/full-operator-v5"
mkdir "$result"
trap 'status=$?; echo "$status" > "$result/run.exit"' EXIT
repo="$task_root/full-plugin-source-v2"
export PYTHONPATH="$repo:$runtime_root/vllm:$task_root:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TASK_QUEUE_ENABLE=1
export TORCHINDUCTOR_CACHE_DIR="$task_root/full-plugin-cache"
export ASCEND_CACHE_PATH="$task_root/full-plugin-cache/ascend"
cd "$repo"
git fetch "$task_root/hc-pre-keyword-fix.bundle" HEAD > "$result/checkout.log" 2>&1
git checkout --detach FETCH_HEAD >> "$result/checkout.log" 2>&1
test "$(git rev-parse HEAD)" = 52c8d05cba1b3b40999dbe473030ed3d29045561
git rev-parse HEAD > "$result/plugin-revision.txt"
git -C "$runtime_root/vllm" rev-parse HEAD > "$result/vllm-revision.txt"
python -m pip freeze > "$result/pip-freeze.txt"
printf '%s\n' "$PYTHONPATH" "$ASCEND_CUSTOM_OPP_PATH" > "$result/runtime-paths.txt"
npu-smi info > "$result/npu-before.txt"
grep -q 'No running processes' "$result/npu-before.txt"
printf '%s\n' 'Full plugin loader and unchanged test file. Collection excludes parent conftest files because FLA dependency is not built. This is not complete nightly/model integration.' > "$result/scope.txt"
export FULL_RESULT_DIR="$result"
FULL_STAGE=tests python "$task_root/full_operator_runner.py" pytest -q --confcutdir=tests/e2e/nightly/single_node/ops/singlecard_ops \
    tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py \
    --junitxml="$result/tests.xml" > "$result/tests.log" 2>&1
npu-smi info > "$result/npu-before-event.txt"
grep -q "No running processes" "$result/npu-before-event.txt"
FULL_STAGE=event python "$task_root/full_operator_runner.py" benchmarks/hc_pre.py --label full-plugin-event --output "$result/event" \
    --reference "$task_root/baseline-a/data" --timing event > "$result/event.log" 2>&1
npu-smi info > "$result/npu-before-graph.txt"
grep -q "No running processes" "$result/npu-before-graph.txt"
FULL_STAGE=graph python "$task_root/full_operator_runner.py" benchmarks/hc_pre.py --label full-plugin-graph --output "$result/graph" \
    --reference "$result/event" --timing graph > "$result/graph.log" 2>&1
npu-smi info > "$result/npu-after.txt"
echo FULL_OPERATOR_VALIDATION_COMPLETE
