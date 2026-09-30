#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
runtime=/mnt/workspace/mhc-validation-20260930
package=$1
variant=$2
program=$3
shift 3
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
case "$package" in
  original) package_path=$task/runtime_baseline ;;
  control) package_path=$task/runtime_baseline_control ;;
  candidate) package_path=$task/runtime_candidate_a3 ;;
  *) exit 2 ;;
esac
export PYTHONPATH="$package_path:$runtime/vllm"
python "$task/probes/$program.py" --variant "$variant" "$@"
