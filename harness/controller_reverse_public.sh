#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
scripts=$task/active-workspace-20261001
results=$task/public-reverse-20261001
previous=$task/public-benchmark-20261001
runtime=/mnt/workspace/mhc-validation-20260930
trap 'status=$?; echo "$status" > "$results/controller.exit"' EXIT
test "$(cat "$task/iteration-e2/acceptance-v1/controller.exit")" = 0
test "$(cat "$previous/controller.exit")" = 0
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
captures=$(python3 - "$previous" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
successful=[f for f in p.glob('capture-attempt-*.exit') if f.read_text().strip()=='0']
assert len(successful)==1
attempt=successful[0].stem.rsplit('-',1)[1]
r=json.loads((p/'capture.json').read_text())
assert r['complete'] and r['all_passed'] and len(r['rows'])==40
print(p/('inputs-attempt-'+attempt))
PY
)
echo "$captures" > "$results/frozen-input-path.txt"
run_json() {
 package=$1;label=$2
 case "$package" in
  control) package_path=$task/runtime_control_e1_v4;variant=baseline ;;
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
  echo "$label attempt $attempt"
  PYTHONPATH="$package_path:$runtime/vllm:$task/probes" python "$scripts/run_checked_v3.py" \
    --expected-runtime "$package_path" --program "$scripts/run_public_benchmark.py" \
    --record "$results/$label-attempt-$attempt-maps.json" --variant "$variant" \
    --phase measure --inputs "$captures" --output "$results/$label-attempt-$attempt.json" \
    > "$results/$label-attempt-$attempt.log" 2>&1 &
  child_pid=$!
  echo "$child_pid" > "$results/$label-attempt-$attempt.pid"
  set +e
  wait "$child_pid"
  status=$?
  set -e
  echo "$status" > "$results/$label-attempt-$attempt.exit"
  if [ "$status" = 0 ];then cp "$results/$label-attempt-$attempt.json" "$results/$label.json";return;fi
  if [ "$status" != 75 ];then return "$status";fi
 done
}
for entry in candidate:c1 control:b1 control:b2 candidate:c2; do
 run_json "${entry%%:*}" "${entry#*:}"
done
echo "Reverse C/B/B/C confirmation completed on all40 default cases using unchanged public benchmark and frozen inputs."
