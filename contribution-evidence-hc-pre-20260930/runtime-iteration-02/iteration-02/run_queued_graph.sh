#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
iteration="$task_root/iteration-02"
variant=${1:?variant}
label=${2:?unique label}
mode=${3:?mode}
registration=${4:-production}
reference=${5:-}
warmup=${6:-20}
source "$runtime_root/venv/bin/activate"
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/Ascend/nnal/atb/set_env.sh"
source "$task_root/$variant/opp/vendors/reduction_${variant}_transformer/bin/set_env.bash"
result="$iteration/$label"
mkdir "$result"
trap 'status=$?; echo "$status" > "$result/run.exit"' EXIT
export PYTHONPATH="$task_root/full-plugin-source-v3:$runtime_root/vllm:$task_root:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TASK_QUEUE_ENABLE=1 ASCEND_LAUNCH_BLOCKING=0
export ASCEND_CUSTOM_OPP_PATH="$task_root/$variant/opp/vendors/reduction_${variant}_transformer:$runtime_root/vllm-ascend/vllm_ascend/_cann_ops_custom/vendors/custom_transformer"
export ASCEND_CACHE_PATH="$iteration/cache-$variant" TORCHINDUCTOR_CACHE_DIR="$iteration/inductor"
repo="$task_root/full-plugin-source-v3"
npu-smi info > "$result/npu-before.txt"
grep -q 'No running processes' "$result/npu-before.txt"
python "$task_root/iteration-01/other_busy.py" > "$result/other-jobs.txt"
ps -eo pid,ppid,etimes,%cpu,args > "$result/processes-before.txt"
extra=()
if [[ -n "$reference" ]]; then extra+=(--reference "$iteration/$reference/data"); fi
case "$mode" in
 boundary)
    python "$iteration/boundary_validation.py" --repo "$repo" --output "$result/data" "${extra[@]}" > "$result/run.log" 2>&1 ;;
 registration)
    python "$iteration/queued_graph_control.py" --repo "$repo" --output "$result/data" --registration "$registration" --warmup "$warmup" --samples 25 --graph-batch 32 "${extra[@]}" > "$result/run.log" 2>&1 ;;
 trace)
    export LD_PRELOAD="$iteration/file_trace.so" HC_PRE_FILE_TRACE="$result/file-opens.tsv"
    export ASCEND_CACHE_PATH="$result/fresh-cache"
    python "$iteration/trace_hc_pre.py" > "$result/run.log" 2>&1
    unset LD_PRELOAD HC_PRE_FILE_TRACE ;;
 *) exit 2 ;;
esac
npu-smi info > "$result/npu-after.txt"
echo "COMPLETED $label"
