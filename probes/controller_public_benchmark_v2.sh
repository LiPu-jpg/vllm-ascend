#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
out=$task/iteration-a2/public-v2
test ! -d "$out"
mkdir "$out"
runtime=/mnt/workspace/mhc-validation-20260930
trap 'status=$?; echo "$status" > "$out/public-benchmark-controller.exit"' EXIT
while [ ! -f "$task/iteration-a2/dcp-controller.exit" ]; do sleep 30; done
test "$(cat "$task/iteration-a2/dcp-controller.exit")" = 0
source "$runtime/Ascend/cann/set_env.sh"
source "$runtime/Ascend/nnal/atb/set_env.sh"
source "$runtime/venv/bin/activate"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
for variant in baseline candidate; do
 attempt=0
 while true; do
  set +e
  python3 "$task/probes/check_window.py" > "$out/public-$variant-window.json"
  status=$?
  set -e
  if [ "$status" = 75 ]; then sleep 30; continue; fi
  test "$status" = 0
  attempt=$((attempt+1))
  if [ "$variant" = baseline ]; then
   export PYTHONPATH="$task/runtime_baseline:$runtime/vllm"
   reference=()
  else
   export PYTHONPATH="$task/runtime_candidate_a2:$runtime/vllm"
   reference=(--reference "$baseline_pt")
  fi
  python "$task/probes/benchmark_sparse_flash_attention_kv_padding.py" --label "$variant-a2" --cases "$task/probes/sparse_flash_attention_perf_cases.jsonl" --output "$out/public-$variant-attempt-$attempt.json" "${reference[@]}" > "$out/public-$variant-attempt-$attempt.log" 2>&1
  set +e
  python3 "$task/probes/check_window.py" > "$out/public-$variant-attempt-$attempt-window.json"
  status=$?
  set -e
  echo "$status" > "$out/public-$variant-attempt-$attempt.exit"
  if [ "$status" = 0 ]; then
   if [ "$variant" = baseline ]; then baseline_pt="$out/public-$variant-attempt-$attempt.pt"; fi
   break
  fi
  if [ "$status" != 75 ]; then exit "$status"; fi
 done
done
