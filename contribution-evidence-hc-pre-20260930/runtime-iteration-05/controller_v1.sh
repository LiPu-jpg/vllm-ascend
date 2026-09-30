#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
iteration="$task_root/iteration-05"
echo "$$" > "$iteration/controller-v1.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v1.exit"' EXIT
source "$runtime_root/venv/bin/activate"
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/Ascend/nnal/atb/set_env.sh"
export PATH="/home/developer/.local/bin:$PATH"
export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13
export C_COMPILER="$CC" CXX_COMPILER="$CXX"
export MAX_JOBS=2 CMAKE_BUILD_PARALLEL_LEVEL=2
# The gate uses live processes, not another task's lock or completion file.
while true; do
    if python "$iteration/foreign_jobs.py" > "$iteration/foreign-current.json"; then
        npu-smi info > "$iteration/npu-current.txt"
        if grep -q 'No running processes' "$iteration/npu-current.txt"; then break; fi
    fi
    sleep 10
done
cp "$iteration/foreign-current.json" "$iteration/foreign-before-build.json"
cp "$iteration/npu-current.txt" "$iteration/npu-before-build.txt"
python "$iteration/build_matched.py" > "$iteration/build.log" 2>&1
python "$iteration/foreign_jobs.py" > "$iteration/foreign-after-build.json"
npu-smi info > "$iteration/npu-after-build.txt"
echo SHORT_DIV_MATCHED_BUILD_COMPLETE
