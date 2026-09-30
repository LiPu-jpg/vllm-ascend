import hashlib
import json
import shutil
from pathlib import Path

root = Path('/mnt/workspace/sfa-nonempty-perf-20260930')
import sys
name=sys.argv[1]
assert name in ('baseline-control','candidate-a3')
assert (root/'iteration-a3'/(name+'-build.exit')).read_text().strip() == '0'
source_file = Path('op_kernel/arch22/sparse_flash_attention_service_vector_mla.h')
generated = root/name/'csrc/build/binary/ascend910b'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inputs = root/'reassessment-20260930'
if name == 'candidate-a3':
    expected = json.loads((inputs/'experiment-manifest.json').read_text())['source_sha256']
else:
    expected = json.loads((inputs/'baseline-source-hashes.json').read_text())[str(source_file)]
assert digest(root/name/'csrc/attention/sparse_flash_attention'/source_file) == expected
assert digest(generated/'src/sparse_flash_attention'/source_file) == expected
assert not (root/('runtime_'+name.replace('-','_'))).exists()
shutil.copytree(root/'runtime_baseline',root/('runtime_'+name.replace('-','_')))
destination = Path('vllm_ascend/_cann_ops_custom/vendors/custom_transformer/op_impl/ai_core/tbe/kernel/ascend910b/sparse_flash_attention')
files = sorted((generated/'bin/sparse_flash_attention').glob('*'))
assert len([p for p in files if p.suffix=='.o']) == 2
record = dict(source_sha256=expected,baseline={},candidate={},shared_libraries={})
for p in files:
    target = root/('runtime_'+name.replace('-','_'))/destination/p.name
    baseline = root/'runtime_baseline'/destination/p.name
    assert baseline.exists()
    record['baseline'][p.name] = digest(baseline)
    shutil.copy2(p,target)
    record['candidate'][p.name] = digest(target)
    if p.suffix=='.o' and name=='candidate-a3':
        assert digest(target)!=digest(baseline)
for p in (root/'runtime_baseline/vllm_ascend').glob('*.so'):
    assert digest(p)==digest(root/('runtime_'+name.replace('-','_'))/'vllm_ascend'/p.name)
    record['shared_libraries'][p.name]=digest(p)
(root/'iteration-a3'/(name+'-kernel-hashes.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
