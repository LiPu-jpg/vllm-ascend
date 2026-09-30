#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-02"
trap 'status=$?; echo "$status" > "$iteration/followup-controller.exit"' EXIT
# The validation controller is a verified live process. Its successful exit
# means all original phases were attempted; inspect each phase result separately.
for check in $(seq 1 720); do
    if [[ -f "$task_root/iteration-01/validation-v4-controller.exit" ]]; then break; fi
    sleep 10
done
test "$(cat "$task_root/iteration-01/validation-v4-controller.exit")" = 0
run() {
    echo "START $*"
    set +e
    bash "$iteration/run_followup.sh" "$@"
    status=$?
    set -e
    printf 'RESULT %s status=%s\n' "$2" "$status"
    if [[ "$status" != 0 && ! -f "$iteration/$2/run.log" ]]; then exit "$status"; fi
}
/usr/bin/gcc-13 -shared -fPIC -O2 "$iteration/file_trace.c" -ldl -o "$iteration/file_trace.so" > "$iteration/trace-build.log" 2>&1
for variant in baseline candidate peeled; do run "$variant" "trace-$variant" trace; done
run baseline boundary-baseline boundary
run peeled boundary-peeled boundary production boundary-baseline
for registration in production historical-probe; do
    for arm in baseline-a candidate-a candidate-b baseline-b; do
        variant=${arm%-*}
        reference=""
        if [[ "$registration-$arm" != production-baseline-a ]]; then reference=production-baseline-a; fi
        run "$variant" "$registration-$arm" registration "$registration" "$reference"
    done
done
for variant in baseline candidate peeled; do
    bash "$task_root/iteration-01/run_profile_v3.sh" "$variant" 1 "profile-v3-$variant-eager" production eager
    bash "$task_root/iteration-01/run_profile_v3.sh" "$variant" 1 "profile-v3-$variant-probe" historical-probe graph
done
echo FOLLOWUP_SEQUENCE_COMPLETED
