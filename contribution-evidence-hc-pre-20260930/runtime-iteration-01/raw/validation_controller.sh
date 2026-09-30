#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-01
trap 'status=$?; echo "$status" > "$iteration/validation-controller.exit"' EXIT
# The existing compiler is kept; wait for its actual exit marker, never restart.
for check in $(seq 1 120); do
    if [[ -f "$iteration/build-peeled/build.exit" ]]; then break; fi
    sleep 10
done
test "$(cat "$iteration/build-peeled/build.exit")" = 0
run() {
    echo "START $*"
    set +e
    bash "$iteration/run_validation.sh" "$@"
    status=$?
    set -e
    printf 'RESULT %s status=%s\n' "$2" "$status"
}
run peeled peeled-production-tests nightly
run baseline baseline-decoder-caller caller
run peeled peeled-decoder-caller caller baseline-decoder-caller
for arm in a1 b1 b2 a2; do run baseline "aa-$arm" graph; done
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    run "$variant" "controlled-$arm" graph aa-a1
done
for arm in baseline-a peeled-a peeled-b baseline-b; do
    variant=${arm%-*}
    run "$variant" "peeled-$arm" graph aa-a1
done
# Leave complete model runs after the fair operator measurements.
run baseline baseline-stock-model-eager model-eager
run peeled peeled-stock-model-eager model-eager
run peeled peeled-stock-model-graph model-graph
echo VALIDATION_SEQUENCE_COMPLETED
