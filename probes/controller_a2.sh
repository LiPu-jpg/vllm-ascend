#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
results=$task/iteration-a2
runtime=/mnt/workspace/mhc-validation-20260930
trap 'status=$?; echo "$status" > "$results/controller.exit"' EXIT
# Never overlap either the previous candidate or its final pytest stage.
while [ ! -f "$task/phase3.exit" ]; do sleep 60; done
test "$(cat "$task/phase3.exit")" = 0
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
  variant=$1
  program=$2
  label=$3
  shift 3
  attempt=0
  while true; do
    wait_window
    attempt=$((attempt+1))
    echo "$label attempt $attempt"
    set +e
    bash "$task/probes/run_program_a2.sh" "$variant" "$program" --output "$results/$label-attempt-$attempt.json" "$@" > "$results/$label-attempt-$attempt.log" 2>&1
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
echo "Candidate A2 build"
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13
export C_COMPILER=/usr/bin/gcc-13 CXX_COMPILER=/usr/bin/g++-13
export OMP_NUM_THREADS=1
cd "$task/candidate-a2/csrc"
set +e
bash build.sh --opkernel --soc=ascend910b --ops=sparse_flash_attention -j2 > "$results/build.log" 2>&1
status=$?
set -e
echo "$status" > "$results/build.exit"
if [ "$status" != 0 ]; then exit "$status"; fi
python "$task/probes/install_a2.py" > "$results/install.log"
run_json candidate experiment correctness-c1 --reference "$task/reference-full-v2"
run_json candidate coverage coverage-c1 --reference "$task/reference-coverage-v3"
for entry in baseline:b2 candidate:c2 candidate:c3 baseline:b3 baseline:b4 candidate:c4; do
  variant=${entry%:*}
  label=${entry#*:}
  run_json "$variant" paired "paired-$label" --reference "$results/reference-paired" --cases "$task/probes/sparse_flash_attention_perf_cases.jsonl"
done
for variant in baseline candidate; do
  attempt=0
  while true; do
    wait_window
    attempt=$((attempt+1))
    echo "Profiler $variant attempt $attempt"
    set +e
    bash "$task/probes/run_program_a2.sh" "$variant" profiler --cases "$task/probes/sparse_flash_attention_perf_cases.jsonl" --trace-root "$results/profiler-$variant-attempt-$attempt" > "$results/profiler-$variant-attempt-$attempt.log" 2>&1
    status=$?
    set -e
    echo "$status" > "$results/profiler-$variant-attempt-$attempt.exit"
    if [ "$status" = 0 ]; then break; fi
    if [ "$status" != 75 ]; then exit "$status"; fi
  done
done
wait_window
export PYTHONPATH="$task/runtime_candidate_a2:$runtime/vllm"
python -m pytest -q "$task/probes/test_sparse_flash_attention_kv_padding.py" --junitxml="$results/pytest-candidate.xml" > "$results/pytest-candidate.log" 2>&1
python3 "$task/probes/check_window.py" > "$results/pytest-window.json"
echo "A2 experiment complete"
