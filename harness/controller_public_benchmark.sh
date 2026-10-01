#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
scripts=$task/active-workspace-20261001
results=$task/public-benchmark-20261001
runtime=/mnt/workspace/mhc-validation-20260930
trap 'status=$?; echo "$status" > "$results/controller.exit"' EXIT
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
run_json() {
 package=$1;label=$2;phase=$3;shift 3
 case "$package" in
  original) package_path=$task/runtime_baseline;variant=baseline ;;
  control) package_path=$task/runtime_control_e1_v4;variant=baseline ;;
  launch_only) package_path=$task/runtime_candidate_e1_v4;variant=candidate ;;
  candidate) package_path=$task/runtime_candidate_e2;variant=candidate ;;
  *) exit 2 ;;
 esac
 attempt=0
 while true; do
  set +e
  python3 "$task/probes/check_window.py" > "$results/current-window.json"
  status=$?
  set -e
  if [ "$status" = 75 ]; then cat "$results/current-window.json" >> "$results/window-waits.jsonl";sleep 60;continue;fi
  if [ "$status" != 0 ]; then return "$status";fi
  attempt=$((attempt+1))
  if [ "$phase" = capture ];then captures=$results/inputs-attempt-$attempt;fi
  echo "$label attempt $attempt"
  set +e
  PYTHONPATH="$package_path:$runtime/vllm:$task/probes" python "$scripts/run_checked_v3.py" \
    --expected-runtime "$package_path" --program "$scripts/run_public_benchmark.py" \
    --record "$results/$label-attempt-$attempt-maps.json" --variant "$variant" \
    --phase "$phase" --inputs "$captures" --output "$results/$label-attempt-$attempt.json" "$@" \
    > "$results/$label-attempt-$attempt.log" 2>&1
  status=$?
  set -e
  echo "$status" > "$results/$label-attempt-$attempt.exit"
  if [ "$status" = 0 ];then cp "$results/$label-attempt-$attempt.json" "$results/$label.json";return;fi
  if [ "$status" != 75 ];then return "$status";fi
 done
}
run_json original capture capture
for entry in control:b1 candidate:c1 candidate:c2 control:b2; do
 run_json "${entry%%:*}" "measure-${entry#*:}" measure
done
for package in control launch_only candidate;do
 run_json "$package" "memory-$package" memory
done
for package in control candidate;do
 run_json "$package" "lse-$package" measure --return-lse
done
echo "Public capture, balanced latency, three-way memory and LSE diagnostics completed; raw failures/retries retained."
