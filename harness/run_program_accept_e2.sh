#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
runtime=/mnt/workspace/mhc-validation-20260930
scripts=$task/active-workspace-20261001
package=$1
variant=$2
program=$3
record=$4
shift 4
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
case "$package" in
  original) package_path=$task/runtime_baseline ;;
  control) package_path=$task/runtime_control_e1_v4 ;;
  candidate) package_path=$task/runtime_candidate_e2 ;;
  *) exit 2 ;;
esac
export PYTHONPATH="$package_path:$runtime/vllm:$task/probes"
case "$program" in
  smoke_d4|pytest_suite|heads_suite|probe_nope_d4) program_path=$scripts/$program.py ;;
  capture_boundaries)
    program_path=$scripts/capture_boundaries_e1.py
    export PYTHONPATH="$PYTHONPATH:$task/diagnosis-20261001/probes_unsorted"
    ;;
  large_index_bounds) program_path=$task/page-index-width-20261001/large_index_bounds.py ;;
  paired_page48) program_path=$task/page-index-width-20261001/probes_page48/paired.py ;;
  paired_unsorted) program_path=$task/diagnosis-20261001/probes_unsorted/paired.py ;;
  indexer_sfa) program_path=$task/diagnosis-20261001/probes_unsorted/indexer_sfa_v2.py ;;
  edge_parity) program_path=$task/merge-index-loop-20261001/edge_parity.py ;;
  experiment|coverage|dcp_receiver|paired) program_path=$task/probes/$program.py ;;
  *) exit 2 ;;
esac
python "$scripts/run_checked_v3.py" --expected-runtime "$package_path" \
  --program "$program_path" --record "$record" --variant "$variant" "$@"
