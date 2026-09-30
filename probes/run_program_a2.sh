#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
runtime=/mnt/workspace/mhc-validation-20260930
variant=$1
program=$2
shift 2
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
if [ "$variant" = candidate ]; then
  export PYTHONPATH="$task/runtime_candidate_a2:$runtime/vllm"
else
  export PYTHONPATH="$task/runtime_baseline:$runtime/vllm"
fi
python "$task/probes/$program.py" --variant "$variant" "$@"
