#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/venv/bin/activate"
export PYTHONPATH="$task_root/full-plugin-source-v2:$runtime_root/vllm:$task_root:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TASK_QUEUE_ENABLE=1
cd "$task_root/full-plugin-source-v2"
test "$(git rev-parse HEAD)" = 52c8d05cba1b3b40999dbe473030ed3d29045561
trap 'status=$?; echo "$status" > "$task_root/full-graph.exit"' EXIT
# The first baseline arm is full-operator-v5/graph, already completed in a
# fresh process immediately before this sequence. Complete the ABBA order.
for arm in candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    result="$task_root/full-graph-$arm"
    mkdir "$result"
    source "$task_root/$variant/opp/vendors/reduction_${variant}_transformer/bin/set_env.bash"
    export ASCEND_CUSTOM_OPP_PATH="$task_root/$variant/opp/vendors/reduction_${variant}_transformer"
    export ASCEND_CACHE_PATH="$task_root/full-graph-cache-$variant"
    npu-smi info > "$result/npu-before.txt"
    grep -q 'No running processes' "$result/npu-before.txt"
    export FULL_RESULT_DIR="$result" FULL_STAGE=graph
    printf '%s\n' "$ASCEND_CUSTOM_OPP_PATH" > "$result/custom-opp-path.txt"
    python "$task_root/full_operator_runner.py" benchmarks/hc_pre.py \
        --label "full-graph-$arm" --output "$result/data" --timing graph \
        --reference "$task_root/full-operator-v5/event" > "$result/benchmark.log" 2>&1
    npu-smi info > "$result/npu-after.txt"
    echo 0 > "$result/run.exit"
done
echo FULL_GRAPH_ABBA_COMPLETE
