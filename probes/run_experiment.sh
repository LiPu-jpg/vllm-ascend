#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
runtime=/mnt/workspace/mhc-validation-20260930
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
variant=$1
label=$2
shift 2
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
export PYTHONPATH="$task/runtime_$variant:$runtime/vllm"
python "$task/probes/experiment.py" --variant "$variant" --output "$task/$label.json" "$@"
