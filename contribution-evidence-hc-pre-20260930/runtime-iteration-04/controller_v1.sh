#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
iteration="$task_root/iteration-04"
echo "$$" > "$iteration/controller-v1.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-v1.exit"' EXIT
source "$runtime_root/venv/bin/activate"
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/Ascend/nnal/atb/set_env.sh"
export PATH="/home/developer/.local/bin:$PATH"
export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13
export C_COMPILER="$CC" CXX_COMPILER="$CXX"
export MAX_JOBS=2 CMAKE_BUILD_PARALLEL_LEVEL=2
python "$task_root/iteration-01/other_busy.py" > "$iteration/other-jobs-before-build.txt"
npu-smi info > "$iteration/npu-before-build.txt"
grep -q 'No running processes' "$iteration/npu-before-build.txt"
python "$iteration/build_matched.py" > "$iteration/build.log" 2>&1
for variant in baseline candidate; do
    bash "$iteration/run_validation.sh" "$variant" "cast1-nightly-$variant" nightly
done
set +e
bash "$iteration/run_validation.sh" baseline cast1-boundary-baseline boundary
baseline_boundary_status=$?
bash "$iteration/run_validation.sh" candidate cast1-boundary-candidate boundary cast1-boundary-baseline
boundary_status=$?
set -e
# Preserve tail cross-process instability; no failing case becomes a pass.
echo "BOUNDARY_BASELINE_STATUS=$baseline_boundary_status"
echo "BOUNDARY_CANDIDATE_STATUS=$boundary_status"
test "$baseline_boundary_status" -le 1
test "$boundary_status" -le 1
python - "$iteration" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
for variant in ('baseline', 'candidate'):
    rows = json.loads((root / f'cast1-boundary-{variant}/data/results.json').read_text())
    assert len(rows) == 60, 'Incomplete boundary run'
    print('BOUNDARY_RESULTS_RETAINED', variant, len(rows),
          sum(row['cpu_accuracy_pass'] for row in rows),
          sum(bool(row['errors']) for row in rows))
PY
for variant in baseline candidate; do
    bash "$iteration/run_validation.sh" "$variant" "cast1-caller-$variant" caller
done
bash "$iteration/run_validation.sh" baseline cast1-graph-baseline-a graph
bash "$iteration/run_validation.sh" candidate cast1-graph-candidate-a graph cast1-graph-baseline-a
bash "$iteration/run_validation.sh" candidate cast1-graph-candidate-b graph cast1-graph-baseline-a
bash "$iteration/run_validation.sh" baseline cast1-graph-baseline-b graph cast1-graph-baseline-a
echo CONTIGUOUS_CAST_INITIAL_VALIDATION_COMPLETE
