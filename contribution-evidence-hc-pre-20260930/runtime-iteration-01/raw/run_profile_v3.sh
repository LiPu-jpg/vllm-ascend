#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
iteration="$task_root/iteration-01"
source "$runtime_root/venv/bin/activate"
source "$runtime_root/Ascend/cann/set_env.sh"
variant=${1:?baseline or candidate}
queue=${2:?queue level}
label=${3:?unique label}
registration=${4:-production}
mode=${5:-graph}
source "$task_root/$variant/opp/vendors/reduction_${variant}_transformer/bin/set_env.bash"
result="$iteration/$label"
mkdir "$result"
trap 'status=$?; echo "$status" > "$result/run.exit"' EXIT
export PYTHONPATH="$task_root/full-plugin-source-v2:$runtime_root/vllm:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TASK_QUEUE_ENABLE="$queue"
export ASCEND_LAUNCH_BLOCKING=0
export ASCEND_CUSTOM_OPP_PATH="$task_root/$variant/opp/vendors/reduction_${variant}_transformer"
export ASCEND_CACHE_PATH="$iteration/profile-cache-$variant"
export TORCHINDUCTOR_CACHE_DIR="$iteration/inductor"
npu-smi info > "$result/npu-before.txt"
grep -q 'No running processes' "$result/npu-before.txt"
python "$iteration/profile_hc_pre_v3.py" --repo "$task_root/full-plugin-source-v2" \
    --output "$result/data" --registration "$registration" --mode "$mode" > "$result/profile.log" 2>&1
npu-smi info > "$result/npu-after.txt"
