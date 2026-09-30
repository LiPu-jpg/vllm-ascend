#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
variant=${1:?baseline or candidate}
mode=${2:?test or benchmark}
label=${3:?unique result label}
reference=${4:-}
timing=${5:-event}
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/venv/bin/activate"
vendor_env=$(find "$task_root/$variant/opp/vendors" -path '*/bin/set_env.bash' -print)
test -f "$vendor_env"
source "$vendor_env"
export CC=/usr/bin/gcc-13 CXX=/usr/bin/g++-13
export MAX_JOBS=2 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export TORCHINDUCTOR_CACHE_DIR="$task_root/inductor"
export ASCEND_CACHE_PATH="$task_root/$variant/cache"
result="$task_root/$label"
export PROBE_RESULT_DIR="$result"
mkdir "$result"
trap 'status=$?; echo "$status" > "$result/run.exit"' EXIT
npu-smi info > "$result/npu-before.txt"
grep -q 'No running processes' "$result/npu-before.txt"
python -m pip freeze > "$result/pip-freeze.txt"
printf '%s\n' "$ASCEND_CUSTOM_OPP_PATH" > "$result/custom-opp-path.txt"
sha256sum "$task_root/$variant/csrc/moe/hc_pre/op_kernel/hc_pre_base.h" \
    "$task_root/probe.py" "$task_root/test_npu_hc_pre.py" "$task_root/hc_pre.py" > "$result/source-sha256.txt"
if [[ "$mode" == test ]]; then
    python "$task_root/probe.py" test --junitxml="$result/tests.xml" > "$result/tests.log" 2>&1
else
    extra=()
    if [[ -n "$reference" ]]; then extra+=(--reference "$task_root/$reference/data"); fi
    python "$task_root/probe.py" benchmark --label "$label" --output "$result/data" \
        --rounds 3 --samples 50 --warmup 20 --timing "$timing" "${extra[@]}" > "$result/benchmark.log" 2>&1
fi
npu-smi info > "$result/npu-after.txt"
