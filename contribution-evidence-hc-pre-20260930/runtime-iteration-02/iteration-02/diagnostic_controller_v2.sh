#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
iteration="$task_root/iteration-02"
trap 'status=$?; echo "$status" > "$iteration/diagnostic-controller-v2.exit"' EXIT
for check in $(seq 1 720); do
    if [[ -f "$iteration/integration-controller-v1.exit" ]]; then break; fi
    sleep 5
done
test -f "$iteration/integration-controller-v1.exit"
test -f "$iteration/full-extension-build-v3/binary-sha256.json"
run() {
    echo "START $*"
    set +e
    bash "$iteration/run_followup_exact3.sh" "$@"
    status=$?
    set -e
    echo "RESULT $2 status=$status"
    # Preserve baseline CPU-oracle failures and compare candidate bitwise.
    # Missing run.log means an idle/environment guard failed, so stop.
    if [[ "$status" != 0 && ! -f "$iteration/$2/run.log" ]]; then exit "$status"; fi
    source /mnt/workspace/mhc-validation-20260930/Ascend/cann/set_env.sh
    npu-smi info > "$iteration/$2/npu-controller-after.txt"
    grep -q 'No running processes' "$iteration/$2/npu-controller-after.txt"
    python "$task_root/iteration-01/other_busy.py" > "$iteration/$2/other-jobs-after.txt"
}
queued_run() {
    echo "QUEUED START $*"
    bash "$iteration/run_queued_graph.sh" "$@"
    source /mnt/workspace/mhc-validation-20260930/Ascend/cann/set_env.sh
    npu-smi info > "$iteration/$2/npu-controller-after.txt"
    grep -q 'No running processes' "$iteration/$2/npu-controller-after.txt"
    python "$task_root/iteration-01/other_busy.py" > "$iteration/$2/other-jobs-after.txt"
}
for arm in a1 b1 b2 a2; do
    reference=""
    if [[ "$arm" != a1 ]]; then reference=queued1-aa-a1; fi
    queued_run baseline "queued1-aa-$arm" registration production "$reference" 10
done
for arm in baseline-a peeled-a peeled-b baseline-b; do
    variant=${arm%-*}
    queued_run "$variant" "queued1-$arm" registration production queued1-aa-a1 10
done
run baseline exact3-boundary-baseline boundary
run peeled exact3-boundary-peeled boundary production exact3-boundary-baseline
for registration in production historical-probe; do
    for arm in baseline-a candidate-a candidate-b baseline-b; do
        variant=${arm%-*}
        reference=""
        if [[ "$registration-$arm" != production-baseline-a ]]; then reference=exact3-production-baseline-a; fi
        run "$variant" "exact3-$registration-$arm" registration "$registration" "$reference" 500
    done
done
for variant in baseline candidate peeled; do
    bash "$iteration/run_profile_exact3.sh" "$variant" 1 "exact3-profile-$variant-eager" production eager
    bash "$iteration/run_profile_exact3.sh" "$variant" 1 "exact3-profile-$variant-probe" historical-probe graph
done
echo SOURCE_EXACT_DIAGNOSTICS_COMPLETE
