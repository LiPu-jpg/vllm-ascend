#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
runtime=/mnt/workspace/mhc-validation-20260930
trap 'status=$?; echo "$status" > "$task/controller-v2.exit"' EXIT
wait_window() {
  while true; do
    set +e
    python3 "$task/probes/check_window.py" > "$task/current-window.json"
    status=$?
    set -e
    if [ "$status" = 0 ]; then return; fi
    if [ "$status" != 75 ]; then return "$status"; fi
    cat "$task/current-window.json" >> "$task/window-waits.jsonl"
    sleep 60
  done
}
run_guarded() {
  variant=$1
  label=$2
  shift 2
  attempt=0
  while true; do
    wait_window
    attempt=$((attempt+1))
    set +e
    bash "$task/probes/run_experiment.sh" "$variant" "$label-attempt-$attempt" "$@" > "$task/$label-attempt-$attempt.log" 2>&1
    status=$?
    set -e
    echo "$status" > "$task/$label-attempt-$attempt.exit"
    if [ "$status" = 0 ]; then
      cp "$task/$label-attempt-$attempt.json" "$task/$label.json"
      return
    fi
    if [ "$status" != 75 ]; then return "$status"; fi
  done
}
echo "Baseline full correctness with explicit empty-row diagnostics"
run_guarded baseline correctness-v2-b1 --reference "$task/reference-full-v2"
wait_window
echo "Candidate kernel build"
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13
export C_COMPILER=/usr/bin/gcc-13 CXX_COMPILER=/usr/bin/g++-13
export OMP_NUM_THREADS=1
cd "$task/candidate/csrc"
set +e
bash build.sh --opkernel --soc=ascend910b --ops=sparse_flash_attention -j2 > "$task/build.log" 2>&1
status=$?
set -e
echo "$status" > "$task/build.exit"
if [ "$status" != 0 ]; then exit "$status"; fi
python "$task/probes/install_candidate.py" > "$task/install.log"
echo "Candidate full correctness"
run_guarded candidate correctness-v2-c1 --reference "$task/reference-full-v2"
echo "Candidate quick measurement"
run_guarded candidate quick-c1 --quick --measure --reference "$task/reference-quick"
echo "Initial experiment complete"
