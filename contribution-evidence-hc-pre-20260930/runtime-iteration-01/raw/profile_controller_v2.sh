#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-01
trap 'status=$?; echo "$status" > "$iteration/profile-v2-controller.exit"' EXIT
for queue in 1 0; do
    for variant in baseline candidate; do
        bash "$iteration/run_profile_v2.sh" "$variant" "$queue" "profile-v2-$variant-q$queue"
    done
done
