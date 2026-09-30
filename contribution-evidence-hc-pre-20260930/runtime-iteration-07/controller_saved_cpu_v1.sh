#!/usr/bin/env bash
set -eo pipefail
iteration=/mnt/workspace/hc-pre-reduction-20260930/iteration-07
echo "$$" > "$iteration/controller-saved-cpu-v1.pid"
trap 'status=$?; echo "$status" > "$iteration/controller-saved-cpu-v1.exit"' EXIT
python3 "$iteration/foreign_jobs.py" > "$iteration/foreign-before-saved-cpu-v1.json"
source /mnt/workspace/mhc-validation-20260930/venv/bin/activate
# CPU sensitivity analysis only. The full production NPU diagnostic is separate.
export TORCH_DEVICE_BACKEND_AUTOLOAD=0 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python "$iteration/diagnose_saved_benchmark_cpu.py" --iteration "$iteration" \
    --output "$iteration/saved-benchmark-cpu-hf32-v1"
python "$iteration/foreign_jobs.py" > "$iteration/foreign-after-saved-cpu-v1.json"
echo SAVED_BENCHMARK_CPU_SENSITIVITY_COMPLETE
