#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-02
trap 'status=$?; echo "$status" > "$iteration/steady-controller.exit"' EXIT
# Preserve the complete short-warmup experiment; a new label is mandatory.
for check in $(seq 1 900); do
    if [[ -f "$iteration/followup-controller.exit" ]]; then break; fi
    sleep 10
done
test -f "$iteration/followup-controller.exit"
run() {
    echo "START $*"
    set +e
    bash "$iteration/run_followup.sh" "$@"
    status=$?
    set -e
    echo "RESULT $2 status=$status"
    if [[ "$status" != 0 ]]; then exit "$status"; fi
}
for arm in a1 b1 b2 a2; do
    reference=""
    if [[ "$arm" != a1 ]]; then reference=steady-aa-a1; fi
    run baseline "steady-aa-$arm" registration production "$reference" 500
done
for arm in baseline-a peeled-a peeled-b baseline-b; do
    variant=${arm%-*}
    run "$variant" "steady-$arm" registration production steady-aa-a1 500
done
echo STEADY_WARMUP_CONTROL_COMPLETE
