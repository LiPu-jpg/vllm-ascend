#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
iteration="$task_root/iteration-07"
echo "$$" > "$iteration/controller-v1.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v1.exit"' EXIT
python "$iteration/foreign_jobs.py" > "$iteration/foreign-before-build.json"
source "$runtime_root/venv/bin/activate"
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/Ascend/nnal/atb/set_env.sh"
npu-smi info > "$iteration/npu-before-build.txt"
grep -q 'No running processes' "$iteration/npu-before-build.txt"
export MAX_JOBS=2 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python "$iteration/build_matched.py"
python "$iteration/foreign_jobs.py" > "$iteration/foreign-after-build.json"
npu-smi info > "$iteration/npu-after-build.txt"
grep -q 'No running processes' "$iteration/npu-after-build.txt"
echo PREFETCH_X_MATCHED_BUILDS_COMPLETE
