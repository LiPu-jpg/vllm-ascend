#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
results=$task/iteration-a3
scripts=$task/reassessment-20260930
runtime=/mnt/workspace/mhc-validation-20260930
trap 'status=$?; echo "$status" > "$results/controller.exit"' EXIT
wait_window() {
  while true; do
    set +e
    python3 "$task/probes/check_window.py" > "$results/current-window.json"
    status=$?
    set -e
    if [ "$status" = 0 ]; then return; fi
    if [ "$status" != 75 ]; then return "$status"; fi
    cat "$results/current-window.json" >> "$results/window-waits.jsonl"
    sleep 60
  done
}
run_json() {
  package=$1
  variant=$2
  program=$3
  label=$4
  shift 4
  attempt=0
  while true; do
    wait_window
    attempt=$((attempt+1))
    echo "$label attempt $attempt"
    set +e
    bash "$scripts/run_program_a3.sh" "$package" "$variant" "$program" --output "$results/$label-attempt-$attempt.json" "$@" > "$results/$label-attempt-$attempt.log" 2>&1
    status=$?
    set -e
    echo "$status" > "$results/$label-attempt-$attempt.exit"
    if [ "$status" = 0 ]; then
      cp "$results/$label-attempt-$attempt.json" "$results/$label.json"
      return
    fi
    if [ "$status" != 75 ]; then return "$status"; fi
  done
}
wait_window
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13
export C_COMPILER=/usr/bin/gcc-13 CXX_COMPILER=/usr/bin/g++-13
export OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
for name in baseline-control candidate-a3; do
  wait_window
  echo "$name build"
  cd "$task/$name/csrc"
  set +e
  bash build.sh --opkernel --soc=ascend910b --ops=sparse_flash_attention -j2 > "$results/$name-build.log" 2>&1
  status=$?
  set -e
  echo "$status" > "$results/$name-build.exit"
  if [ "$status" != 0 ]; then exit "$status"; fi
  python "$scripts/install_a3.py" "$name" > "$results/$name-install.log"
done
for package in control candidate; do
  run_json "$package" candidate experiment "correctness-$package" --reference "$task/reference-full-v2"
  run_json "$package" candidate coverage "coverage-$package" --reference "$task/reference-coverage-v3"
  # Coverage intentionally records existing reference failures. Require byte
  # parity for every output; retain those failures instead of suppressing them.
  python - "$results/coverage-$package.json" <<'PY'
import json,sys
rows=json.load(open(sys.argv[1]))['rows']
assert len(rows)==98
assert all(all(r['bytewise_baseline_by_output']) for r in rows if 'bytewise_baseline_by_output' in r)
PY
  run_json "$package" candidate dcp_receiver "dcp-$package" --reference "$task/iteration-a2/reference-dcp"
done
# Separately preserve the original-installation/rebuilt-control comparison.
run_json original baseline paired build-control-original --reference "$results/reference-control" --cases "$task/probes/sparse_flash_attention_perf_cases.jsonl"
run_json control candidate paired build-control-rebuilt --reference "$results/reference-control" --cases "$task/probes/sparse_flash_attention_perf_cases.jsonl"
for entry in control:baseline:b2 candidate:candidate:c2 candidate:candidate:c3 control:baseline:b3 control:baseline:b4 candidate:candidate:c4; do
  package=${entry%%:*}
  rest=${entry#*:}
  variant=${rest%%:*}
  label=${rest#*:}
  run_json "$package" "$variant" paired "paired-$label" --reference "$results/reference-control" --cases "$task/probes/sparse_flash_attention_perf_cases.jsonl"
done
for package in control candidate; do
  attempt=0
  while true; do
    wait_window
    attempt=$((attempt+1))
    set +e
    bash "$scripts/run_program_a3.sh" "$package" candidate profiler --cases "$task/probes/sparse_flash_attention_perf_cases.jsonl" --trace-root "$results/profiler-$package-attempt-$attempt" > "$results/profiler-$package-attempt-$attempt.log" 2>&1
    status=$?
    set -e
    echo "$status" > "$results/profiler-$package-attempt-$attempt.exit"
    if [ "$status" = 0 ]; then break; fi
    if [ "$status" != 75 ]; then exit "$status"; fi
  done
  wait_window
  if [ "$package" = control ]; then package_path=$task/runtime_baseline_control; else package_path=$task/runtime_candidate_a3; fi
  export PYTHONPATH="$package_path:$runtime/vllm"
  python -m pytest -q "$task/probes/test_sparse_flash_attention_kv_padding.py" --junitxml="$results/pytest-$package.xml" > "$results/pytest-$package.log" 2>&1
  python3 "$task/probes/check_window.py" > "$results/pytest-$package-window.json"
done
echo "Third candidate and rebuilt-control experiment complete"
