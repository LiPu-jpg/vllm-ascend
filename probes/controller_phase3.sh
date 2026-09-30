#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
runtime=/mnt/workspace/mhc-validation-20260930
trap 'status=$?; echo "$status" > "$task/phase3.exit"' EXIT
while [ ! -f "$task/phase2-v3.exit" ]; do sleep 60; done
test "$(cat "$task/phase2-v3.exit")" = 0
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
wait_window() {
  while true; do
    set +e
    python3 "$task/probes/check_window.py" > "$task/current-window-phase3.json"
    status=$?
    set -e
    if [ "$status" = 0 ]; then return; fi
    if [ "$status" != 75 ]; then return "$status"; fi
    cat "$task/current-window-phase3.json" >> "$task/window-waits.jsonl"
    sleep 60
  done
}
for variant in baseline candidate; do
  attempt=0
  while true; do
    wait_window
    attempt=$((attempt+1))
    export PYTHONPATH="$task/runtime_$variant:$runtime/vllm"
    echo "Native pytest $variant attempt $attempt"
    set +e
    python -m pytest -q "$task/probes/test_sparse_flash_attention_kv_padding.py" --junitxml="$task/pytest-$variant-attempt-$attempt.xml" > "$task/pytest-$variant-attempt-$attempt.log" 2>&1
    status=$?
    python3 "$task/probes/check_window.py" > "$task/pytest-$variant-attempt-$attempt-window.json"
    guard_status=$?
    set -e
    echo "$status" > "$task/pytest-$variant-attempt-$attempt.exit"
    if [ "$guard_status" = 75 ]; then continue; fi
    if [ "$guard_status" != 0 ]; then exit "$guard_status"; fi
    if [ "$status" != 0 ]; then exit "$status"; fi
    break
  done
done
wait_window
export PYTHONPATH="$task/runtime_candidate:$runtime/vllm"
python "$task/probes/verify_benchmark.py" > "$task/verify-benchmark.log" 2>&1
echo "Phase 3 complete"
