#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
out=$task/iteration-a2
trap 'status=$?; echo "$status" > "$out/dcp-controller.exit"' EXIT
while [ ! -f "$out/controller.exit" ]; do sleep 30; done
test "$(cat "$out/controller.exit")" = 0
for variant in baseline candidate; do
 attempt=0
 while true; do
  set +e
  python3 "$task/probes/check_window.py" > "$out/dcp-window.json"
  status=$?
  set -e
  if [ "$status" = 75 ]; then sleep 30; continue; fi
  test "$status" = 0
  attempt=$((attempt+1))
  set +e
  bash "$task/probes/run_program_a2.sh" "$variant" dcp_receiver --output "$out/dcp-$variant-attempt-$attempt.json" --reference "$out/reference-dcp" > "$out/dcp-$variant-attempt-$attempt.log" 2>&1
  status=$?
  set -e
  echo "$status" > "$out/dcp-$variant-attempt-$attempt.exit"
  if [ "$status" = 0 ]; then break; fi
  if [ "$status" != 75 ]; then exit "$status"; fi
 done
done
