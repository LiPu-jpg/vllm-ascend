#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-02
trap 'status=$?; echo "$status" > "$iteration/idle-controls-v1.exit"' EXIT
run() {
    echo "START $*"
    bash "$iteration/run_followup.sh" "$@"
    echo "RESULT $2 status=0"
    source /mnt/workspace/mhc-validation-20260930/Ascend/cann/set_env.sh
    npu-smi info > "$iteration/$2/npu-controller-after.txt"
    grep -q 'No running processes' "$iteration/$2/npu-controller-after.txt"
    python3 /mnt/workspace/hc-pre-reduction-20260930/iteration-01/other_busy.py > "$iteration/$2/other-jobs-after.txt"
}
/usr/bin/gcc-13 -shared -fPIC -O2 "$iteration/file_trace.c" -ldl -o "$iteration/file_trace.so" > "$iteration/idle-trace-build.log" 2>&1
for variant in baseline candidate peeled; do run "$variant" "idle1-trace-$variant" trace; done
for arm in a1 b1 b2 a2; do
    reference=""
    if [[ "$arm" != a1 ]]; then reference=idle1-aa-a1; fi
    run baseline "idle1-aa-$arm" registration production "$reference" 500
done
for arm in baseline-a peeled-a peeled-b baseline-b; do
    variant=${arm%-*}
    run "$variant" "idle1-$arm" registration production idle1-aa-a1 500
done
echo IDLE_CONTROLS_COMPLETE
