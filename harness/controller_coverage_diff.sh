#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
scripts=$task/active-workspace-20261001
results=$task/coverage-byte-diagnostic-20261001
runtime=/mnt/workspace/mhc-validation-20260930
trap 'status=$?; echo "$status" > "$results/controller.exit"' EXIT
test "$(cat "$task/reference-controls-20261001/controller.exit")" = 0
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
for package in control candidate; do
 case "$package" in
  control) package_path=$task/runtime_control_e1_v4;variant=baseline ;;
  candidate) package_path=$task/runtime_candidate_e2;variant=candidate ;;
 esac
 attempt=0
 while true; do
  set +e
  python3 "$task/probes/check_window.py" > "$results/current-window.json"
  status=$?
  set -e
  if [ "$status" = 75 ];then cat "$results/current-window.json" >> "$results/window-waits.jsonl";sleep 30;continue;fi
  if [ "$status" != 0 ];then exit "$status";fi
  attempt=$((attempt+1))
  echo "$package attempt $attempt"
  PYTHONPATH="$package_path:$runtime/vllm:$task/probes" python "$scripts/run_checked_v3.py" \
    --expected-runtime "$package_path" --program "$scripts/probe_coverage_byte_differences.py" \
    --record "$results/$package-attempt-$attempt-maps.json" --variant "$variant" \
    --reference "$task/reference-coverage-v3" --coverage-source "$task/probes/coverage.py" \
    --output "$results/$package-attempt-$attempt.json" > "$results/$package-attempt-$attempt.log" 2>&1 &
  child_pid=$!
  echo "$child_pid" > "$results/$package-attempt-$attempt.pid"
  set +e
  wait "$child_pid"
  status=$?
  set -e
  echo "$status" > "$results/$package-attempt-$attempt.exit"
  if [ "$status" = 0 ];then cp "$results/$package-attempt-$attempt.json" "$results/$package.json";break;fi
  if [ "$status" != 75 ];then exit "$status";fi
 done
done
echo "All96 legacy configurations captured twice per original/candidate package; frozen references unchanged."
