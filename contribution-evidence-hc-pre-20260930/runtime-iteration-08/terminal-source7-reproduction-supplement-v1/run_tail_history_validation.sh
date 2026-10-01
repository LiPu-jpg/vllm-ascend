#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
iteration="$task_root/iteration-08"
variant=${1:?variant}
label=${2:?unique label}
mode=${3:?mode}
reference=${4:-}
source "$runtime_root/venv/bin/activate"
python "$iteration/foreign_jobs.py" > "$iteration/foreign-before-tail-history-$variant.json"
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/Ascend/nnal/atb/set_env.sh"
source "$task_root/batch-comb-source-$variant/opp/vendors/batch_comb_${variant}_transformer/bin/set_env.bash"
result="$iteration/$label"
mkdir "$result"
finalize_validation() {
    validation_status=$?
    trap - EXIT
    set +e
    npu-smi info > "$result/npu-after.txt" 2>&1
    npu_query_status=$?
    grep -q 'No running processes' "$result/npu-after.txt"
    npu_idle_status=$?
    python "$task_root/iteration-01/other_busy.py" > "$result/other-jobs-after.txt" 2>&1
    other_jobs_status=$?
    python "$iteration/foreign_jobs.py" > "$result/foreign-after.json" 2>&1
    foreign_jobs_status=$?
    printf '{"npu_query":%s,"npu_idle":%s,"other_jobs":%s,"foreign_jobs":%s}\n' \
        "$npu_query_status" "$npu_idle_status" "$other_jobs_status" "$foreign_jobs_status" \
        > "$result/guards-after-status.json"
    if [[ "$validation_status" == 0 && \
          ( "$npu_query_status" != 0 || "$npu_idle_status" != 0 || \
            "$other_jobs_status" != 0 || "$foreign_jobs_status" != 0 ) ]]; then
        validation_status=75
    fi
    echo "$validation_status" > "$result/run.exit"
    exit "$validation_status"
}
trap finalize_validation EXIT
repo="$task_root/batch-comb-source-$variant"
export PYTHONPATH="$task_root/iteration-01:$iteration:$repo:$runtime_root/vllm:$task_root:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TASK_QUEUE_ENABLE=1 ASCEND_LAUNCH_BLOCKING=0
export ASCEND_CUSTOM_OPP_PATH="$task_root/batch-comb-source-$variant/opp/vendors/batch_comb_${variant}_transformer:$runtime_root/vllm-ascend/vllm_ascend/_cann_ops_custom/vendors/custom_transformer"
export ASCEND_CACHE_PATH="$iteration/cache-$variant" TORCHINDUCTOR_CACHE_DIR="$iteration/inductor"
export FULL_RESULT_DIR="$result" FULL_STAGE="$mode"
npu-smi info > "$result/npu-before.txt"
grep -q 'No running processes' "$result/npu-before.txt"
python "$task_root/iteration-01/other_busy.py" > "$result/other-jobs.txt"
python "$iteration/foreign_jobs.py" > "$result/foreign-before.json"
git -C "$repo" status --short > "$result/source-status.txt"
git -C "$repo" rev-parse HEAD > "$result/source-head.txt"
cd "$repo"
extra=()
if [[ -n "$reference" ]]; then extra+=(--reference "$iteration/$reference/data"); fi
# Check actual private kernel selection before the first timed arm per variant.
# The tracer is confined to its own process/cache; timing has no LD_PRELOAD.
if [[ "$label" == batch-comb1-graph-baseline-a || "$label" == batch-comb1-graph-candidate-a ]]; then
    diagnostic="$result/pre-timing-kernel-selection"
    mkdir "$diagnostic"
    env LD_PRELOAD="$task_root/iteration-02/file_trace.so" \
        HC_PRE_FILE_TRACE="$diagnostic/file-opens.tsv" \
        ASCEND_CACHE_PATH="$diagnostic/fresh-cache" \
        python "$iteration/trace_v2.py" > "$diagnostic/run.log" 2>&1
    python "$iteration/verify_kernel_selection.py" "$repo" \
        "$iteration/full-extension-build-$variant/binary-sha256.json" \
        "$diagnostic/opened-kernels.json" > "$diagnostic/verification.log"
    npu-smi info > "$diagnostic/npu-after.txt"
    grep -q 'No running processes' "$diagnostic/npu-after.txt"
fi
case "$mode" in
  tail-history)
    python "$task_root/full_operator_runner.py" "$iteration/tail_history_diagnostics.py" --oracle "$iteration/test_npu_hc_pre_hf32_reference.py" --output "$result/data" > "$result/run.log" 2>&1 ;;
  nightly)
    # Collect through the normal repository conftests. The baseline gets only
    # the identical test update; its runtime sources and extension stay intact.
    test_path=tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py
    cp "$test_path" "$result/upstream-test.py"
    cp "$iteration/test_npu_hc_pre_hf32_reference.py" "$test_path"
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
    python "$task_root/full_operator_runner.py" "$iteration/hc_pre_v2.py" --api v2 --label "$label" --output "$result/data" --timing "$mode" --graph-batch "$graph_batch" --warmup 10 --samples 25 --rounds 3 "${extra[@]}" > "$result/run.log" 2>&1 ;;
  boundary)
    python "$iteration/optional_output_boundary.py" --repo "$repo" --oracle "$iteration/test_npu_hc_pre_hf32_reference.py" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  profile-eager|profile-graph)
    python "$iteration/profile_hc_pre_v2.py" --repo "$repo" --output "$result/data" --registration production --mode "${mode#profile-}" > "$result/run.log" 2>&1 ;;
  trace)
    export LD_PRELOAD="$task_root/iteration-02/file_trace.so" HC_PRE_FILE_TRACE="$result/file-opens.tsv"
    export ASCEND_CACHE_PATH="$result/fresh-cache"
    python "$iteration/trace_v2.py" > "$result/run.log" 2>&1
    unset LD_PRELOAD HC_PRE_FILE_TRACE ;;
  fixture)
    python "$iteration/finite_fixture_diagnostics.py" --repo "$repo" --oracle "$iteration/test_npu_hc_pre_hf32_reference.py" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  benchmark-fixture)
    python "$iteration/benchmark_fixture_diagnostics.py" --repo "$repo" --oracle "$iteration/test_npu_hc_pre_hf32_reference.py" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  caller)
    python "$iteration/glm_native_caller_hf32_reference.py" --repo "$repo" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  model-eager|model-graph)
    extra=()
    if [[ "$mode" == model-graph ]]; then extra+=(--graph); fi
    python "$task_root/iteration-02/glm_stock_dummy_smoke_profile.py" --repo "$repo" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
  *) exit 2 ;;
esac
echo "PROGRAM_COMPLETED $label"
