#!/usr/bin/env bash
set -eo pipefail
task=/mnt/workspace/sfa-nonempty-perf-20260930
scripts=$task/active-workspace-20261001
screen=$task/iteration-e2/screen-v1
results=$task/iteration-e2/acceptance-v1
trap 'status=$?; echo "$status" > "$results/controller.exit"' EXIT
test "$(cat "$screen/screen-controller.exit")" = 0
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
  package=$1; variant=$2; program=$3; label=$4
  shift 4
  attempt=0
  while true; do
    wait_window
    attempt=$((attempt+1))
    echo "$label attempt $attempt"
    extra=()
    if [ "$program" = heads_suite ]; then
      extra+=(--junitxml "$results/$label-attempt-$attempt.xml")
    fi
    if [ "$program" = capture_boundaries ]; then
      reference=$results/reference-indexer-boundaries-attempt-$attempt
      extra+=(--reference "$reference")
    fi
    if [ "$label" = boundary-capture ]; then
      reference=$results/reference-nope-boundaries-attempt-$attempt
      extra+=(--reference "$reference")
    fi
    set +e
    bash "$scripts/run_program_accept_e2.sh" "$package" "$variant" "$program" \
      "$results/$label-attempt-$attempt-maps.json" \
      --output "$results/$label-attempt-$attempt.json" "${extra[@]}" "$@" \
      > "$results/$label-attempt-$attempt.log" 2>&1
    status=$?
    set -e
    echo "$status" > "$results/$label-attempt-$attempt.exit"
    if [ "$status" = 0 ]; then
      cp "$results/$label-attempt-$attempt.json" "$results/$label.json"
      if [ "$program" = capture_boundaries ]; then echo "$reference" > "$results/indexer-boundary-path.txt"; fi
      if [ "$label" = boundary-capture ]; then echo "$reference" > "$results/nope-boundary-path.txt"; fi
      return
    fi
    if [ "$status" != 75 ]; then return "$status"; fi
  done
}
run_json control baseline heads_suite full-tests-control
run_json candidate candidate heads_suite full-tests-candidate
run_json candidate candidate experiment correctness-candidate --reference "$task/reference-full-v2"
run_json candidate candidate coverage coverage-candidate --reference "$task/reference-coverage-v3"
run_json candidate candidate dcp_receiver dcp-candidate --reference "$task/iteration-a2/reference-dcp"
run_json candidate candidate edge_parity edges-candidate --reference "$task/iteration-d1/reference-edge-parity"
run_json control baseline large_index_bounds large-bounds-control --reference "$results/reference-large-bounds"
run_json candidate candidate large_index_bounds large-bounds-candidate --reference "$results/reference-large-bounds"
# Indexer capture needs the full original host registration package, not the SFA-only component runtimes.
run_json original baseline capture_boundaries indexer-boundaries
captures=$(cat "$results/indexer-boundary-path.txt")
run_json control baseline probe_nope_d4 boundary-capture --phase capture --captures "$captures" \
  --query-counts 2 4 9 10 11 12 13 16 19 20 21 24
reference=$(cat "$results/nope-boundary-path.txt")
run_json candidate candidate probe_nope_d4 boundary-check --phase check --captures "$captures" \
  --reference "$reference" --query-counts 2 4 9 10 11 12 13 16 19 20 21 24
for entry in control:baseline:b1 candidate:candidate:c1 candidate:candidate:c2 control:baseline:b2; do
  package=${entry%%:*}; rest=${entry#*:}; variant=${rest%%:*}; label=${rest#*:}
  run_json "$package" "$variant" probe_nope_d4 "boundary-$label" --phase measure --captures "$captures" \
    --reference "$reference" --query-counts 2 4 9 10 11 12 13 16 19 20 21 24
done
# Keep every case from the previous 172-case matrix, including short selected prefixes and page48.
for dataset in paired unsorted indexer page48; do
  case "$dataset" in
    paired) program=paired; reference=$results/reference-paired; cases=$task/probes/sparse_flash_attention_perf_cases.jsonl ;;
    unsorted) program=paired_unsorted; reference=$task/diagnosis-20261001/reference-unsorted; cases=$task/diagnosis-20261001/probes_unsorted/sparse_flash_attention_perf_cases.jsonl ;;
    indexer) program=indexer_sfa; reference=$task/diagnosis-20261001/reference-indexer ;;
    page48) program=paired_page48; reference=$results/reference-page48; cases=$task/page-index-width-20261001/probes_page48/sparse_flash_attention_perf_cases.jsonl ;;
  esac
  for entry in control:baseline:b1 candidate:candidate:c1 candidate:candidate:c2 control:baseline:b2; do
    package=${entry%%:*}; rest=${entry#*:}; variant=${rest%%:*}; label=${rest#*:}
    extra=()
    if [ "$program" = heads_suite ]; then
      extra+=(--junitxml "$results/$label-attempt-$attempt.xml")
    fi
    if [ "$dataset" != indexer ]; then extra+=(--cases "$cases"); fi
    run_json "$package" "$variant" "$program" "$dataset-$label" --reference "$reference" "${extra[@]}"
  done
done
python "$scripts/analyze_nope_boundaries_e1.py" --results "$results" --prefix boundary --query-counts 2 4 9 10 11 12 13 16 19 20 21 24 --output "$results/boundary-analysis.json"
echo "Additional 192 NoPE boundary records and all original 172 cases complete; reverse acceptance and physical A3 remain unverified"
