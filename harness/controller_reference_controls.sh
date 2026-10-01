#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
scripts=$task/active-workspace-20261001
results=$task/reference-controls-20261001
trap 'status=$?; echo "$status" > "$results/controller.exit"' EXIT
test "$(cat "$task/public-reverse-20261001/controller.exit")" = 0
run_json() {
 program=$1;label=$2;reference=$3
 attempt=0
 while true; do
  set +e
  python3 "$task/probes/check_window.py" > "$results/current-window.json"
  status=$?
  set -e
  if [ "$status" = 75 ];then cat "$results/current-window.json" >> "$results/window-waits.jsonl";sleep 60;continue;fi
  if [ "$status" != 0 ];then return "$status";fi
  attempt=$((attempt+1))
  echo "$label attempt $attempt"
  set +e
  # The legacy program's candidate mode means read-only replay against a frozen
  # reference. The installed package here is always the original control build.
  bash "$scripts/run_program_accept_e2.sh" control candidate "$program" \
   "$results/$label-attempt-$attempt-maps.json" --reference "$reference" \
   --output "$results/$label-attempt-$attempt.json" \
   > "$results/$label-attempt-$attempt.log" 2>&1
  status=$?
  set -e
  echo "$status" > "$results/$label-attempt-$attempt.exit"
  if [ "$status" = 0 ];then cp "$results/$label-attempt-$attempt.json" "$results/$label.json";return;fi
  if [ "$status" != 75 ];then return "$status";fi
 done
}
run_json coverage coverage-control-replay "$task/reference-coverage-v3"
run_json edge_parity edges-control-replay "$task/iteration-d1/reference-edge-parity"
echo "Fresh original control replayed every legacy coverage/partial-block case; all baseline oracle failures remain recorded."
