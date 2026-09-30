#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-01
trap 'status=$?; echo "$status" > "$iteration/validation-v2-controller.exit"' EXIT
# Read-only wait for both known competing controllers; do not kill or restart.
for check in $(seq 1 360); do
    busy=0
    for competing_pid in 1053063 1053422; do
        if [[ -r /proc/$competing_pid/cmdline ]]; then
            competing_command=$(tr '\0' ' ' < /proc/$competing_pid/cmdline)
            if [[ "$competing_command" == *finish_v32.sh* || "$competing_command" == *run_model_comparison_v32.sh* ]]; then busy=1; fi
        fi
    done
    if [[ "$busy" == 0 ]]; then break; fi
    if (( check % 6 == 1 )); then date -u '+WAIT competing model controllers %FT%TZ'; fi
    sleep 10
done
test "$busy" = 0
test "$(cat "$iteration/build-peeled/build.exit")" = 0
run() {
    echo "START $*"
    set +e
    bash "$iteration/run_validation.sh" "$@"
    status=$?
    set -e
    printf 'RESULT %s status=%s\n' "$2" "$status"
    if [[ "$status" != 0 && ! -f "$iteration/$2/run.log" ]]; then
        echo "STOP idle guard or setup failure; no further device work"
        exit "$status"
    fi
}
run peeled v2-peeled-production-tests nightly
run baseline v2-baseline-decoder-caller caller
run peeled v2-peeled-decoder-caller caller v2-baseline-decoder-caller
for arm in a1 b1 b2 a2; do run baseline "v2-aa-$arm" graph; done
for arm in baseline-a candidate-a candidate-b baseline-b; do
    variant=${arm%-*}
    run "$variant" "v2-controlled-$arm" graph v2-aa-a1
done
for arm in baseline-a peeled-a peeled-b baseline-b; do
    variant=${arm%-*}
    run "$variant" "v2-peeled-$arm" graph v2-aa-a1
done
# Leave complete model runs after the fair operator measurements.
run baseline v2-baseline-stock-model-eager model-eager
run peeled v2-peeled-stock-model-eager model-eager
run peeled v2-peeled-stock-model-graph model-graph
echo VALIDATION_SEQUENCE_COMPLETED
