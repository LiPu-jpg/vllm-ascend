#!/usr/bin/env bash
set -eo pipefail
task_root=/mnt/workspace/hc-pre-reduction-20260930
runtime_root=/mnt/workspace/mhc-validation-20260930
source "$runtime_root/Ascend/cann/set_env.sh"
source "$runtime_root/Ascend/nnal/atb/set_env.sh"
source "$runtime_root/venv/bin/activate"
source "$task_root/baseline/opp/vendors/reduction_baseline_transformer/bin/set_env.bash"
result="$task_root/full-plugin-v2"
mkdir "$result"
trap 'status=$?; echo "$status" > "$result/run.exit"' EXIT
repo="$task_root/full-plugin-source-v2"
git clone --shared --no-checkout "$runtime_root/vllm-ascend" "$repo" > "$result/checkout.log" 2>&1
git -C "$repo" fetch "$task_root/hc-pre-pr.bundle" HEAD >> "$result/checkout.log" 2>&1
git -C "$repo" checkout --detach FETCH_HEAD >> "$result/checkout.log" 2>&1
test "$(git -C "$repo" rev-parse HEAD)" = 4fc47457d8a0300f386291afb15fb75a77605410
cp "$runtime_root/vllm-ascend/vllm_ascend/"*.so "$repo/vllm_ascend/"
cp "$runtime_root/vllm-ascend/vllm_ascend/_build_info.py" "$repo/vllm_ascend/"
cp "$runtime_root/vllm-ascend/vllm_ascend/_version.py" "$repo/vllm_ascend/"
export PYTHONPATH="$repo:$runtime_root/vllm:$task_root:${PYTHONPATH:-}"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TASK_QUEUE_ENABLE=1
export TORCHINDUCTOR_CACHE_DIR="$task_root/full-plugin-cache"
export ASCEND_CACHE_PATH="$task_root/full-plugin-cache/ascend"
cd "$repo"
git rev-parse HEAD > "$result/plugin-revision.txt"
git -C "$runtime_root/vllm" rev-parse HEAD > "$result/vllm-revision.txt"
git -C "$runtime_root/vllm-ascend" rev-parse HEAD > "$result/reused-extension-source-revision.txt"
python -m pip freeze > "$result/pip-freeze.txt"
sha256sum vllm_ascend/*.so > "$result/extension-sha256.txt"
python - "$repo" "$runtime_root/vllm-ascend" <<'PY' > "$result/binding-source-check.txt"
import hashlib
import sys
from pathlib import Path
def section(repo):
    source = (Path(repo) / 'csrc/torch_binding.cpp').read_text()
    begin = source.index('constexpr int64_t HC_PRE_HC_LIMIT = 4;')
    end = source.index('\nvoid inplace_partial_rotary_mul_npu', begin)
    return source[begin:end]
a, b = map(section, sys.argv[1:])
assert a == b, 'Reused extension HcPre source differs'
print('Unchanged HcPre binding SHA256:', hashlib.sha256(a.encode()).hexdigest())
print('Other operators in reused extension are outside this validation scope.')
PY
npu-smi info > "$result/npu-before.txt"
grep -q 'No running processes' "$result/npu-before.txt"
python - <<'PY' > "$result/import.log" 2>&1
import torch, torch_npu
import vllm, vllm_ascend
from vllm_ascend.utils import enable_custom_op
print('vllm:', vllm.__file__)
print('plugin:', vllm_ascend.__file__)
assert enable_custom_op()
import vllm_ascend.vllm_ascend_C as extension
print('extension:', extension.__file__)
print('HcPre:', torch.ops._C_ascend.npu_hc_pre_v3)
PY
python -m pytest -q tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py \
    --junitxml="$result/tests.xml" > "$result/tests.log" 2>&1
python benchmarks/hc_pre.py --label full-plugin-event --output "$result/event" \
    --reference "$task_root/baseline-a/data" --timing event > "$result/event.log" 2>&1
python benchmarks/hc_pre.py --label full-plugin-graph --output "$result/graph" \
    --reference "$result/event" --timing graph > "$result/graph.log" 2>&1
npu-smi info > "$result/npu-after.txt"
echo FULL_PLUGIN_HC_PRE_VALIDATION_COMPLETE
