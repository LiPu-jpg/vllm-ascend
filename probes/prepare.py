import hashlib
import json
import shutil
import tarfile
from pathlib import Path

root = Path('/mnt/workspace/sfa-nonempty-perf-20260930')
assert not (root/'runtime_baseline').exists()
shutil.copytree('/mnt/workspace/sfa-upstream-20260930/runtime',root/'runtime_baseline')
with tarfile.open(root/'candidate-csrc.tar.gz') as archive:
    archive.extractall(root/'candidate',filter='data')
hashes=json.loads((root/'expected-baseline-kernels.json').read_text())
kernel=root/'runtime_baseline/vllm_ascend/_cann_ops_custom/vendors/custom_transformer/op_impl/ai_core/tbe/kernel/ascend910b/sparse_flash_attention'
for name, expected in hashes.items():
    assert hashlib.sha256((kernel/name).read_bytes()).hexdigest()==expected, name
print('Independent baseline snapshot and candidate source prepared; baseline artifact hashes verified.')
