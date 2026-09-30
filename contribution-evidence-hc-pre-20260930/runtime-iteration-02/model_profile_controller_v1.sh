#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-02
trap 'status=$?; echo "$status" > "$iteration/model-profile-controller-v1.exit"' EXIT
for check in $(seq 1 1440); do
    if [[ -f "$iteration/diagnostic-controller-v2.exit" ]]; then break; fi
    sleep 5
done
test -f "$iteration/diagnostic-controller-v2.exit"
for variant in baseline peeled; do
    bash "$iteration/run_model_profile.sh" "$variant" "model-profile1-$variant-graph" model-graph
done
echo MODEL_GRAPH_TRACE_COLLECTION_COMPLETE
