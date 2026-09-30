#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
trap 'status=$?; echo "$status" > "$task/phase2.exit"' EXIT
test "$(cat "$task/controller-v2.exit")" = 0
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
    bash "$task/probes/run_program.sh" "$variant" "$program" --output "$task/$label-attempt-$attempt.json" "$@" > "$task/$label-attempt-$attempt.log" 2>&1
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
run_json baseline coverage coverage-b1 --reference "$task/reference-coverage"
run_json candidate coverage coverage-c1 --reference "$task/reference-coverage"
for entry in baseline:b2 candidate:c2 candidate:c3 baseline:b3 baseline:b4 candidate:c4; do
  variant=${entry%:*}
  label=${entry#*:}
  run_json "$variant" paired "paired-$label" --reference "$task/reference-paired" --cases "$task/probes/sparse_flash_attention_perf_cases.jsonl"
done
for variant in baseline candidate; do
  attempt=0
  while true; do
    wait_window
    attempt=$((attempt+1))
    echo "Profiler $variant attempt $attempt"
    set +e
    bash "$task/probes/run_program.sh" "$variant" profiler --cases "$task/probes/sparse_flash_attention_perf_cases.jsonl" --trace-root "$task/profiler-$variant-attempt-$attempt" > "$task/profiler-$variant-attempt-$attempt.log" 2>&1
    status=$?
    set -e
    echo "$status" > "$task/profiler-$variant-attempt-$attempt.exit"
    if [ "$status" = 0 ]; then break; fi
    if [ "$status" != 75 ]; then exit "$status"; fi
  done
done
echo "Phase 2 complete"
