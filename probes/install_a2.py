import hashlib
import json
import shutil
from pathlib import Path

root = Path('/mnt/workspace/sfa-nonempty-perf-20260930')
assert (root/'iteration-a2/build.exit').read_text().strip() == '0'
source_file = Path('op_kernel/arch22/sparse_flash_attention_service_vector_mla.h')
generated = root/'candidate-a2/csrc/build/binary/ascend910b'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
expected = (root/'candidate-a2-source.sha256').read_text().strip()
assert digest(root/'candidate-a2/csrc/attention/sparse_flash_attention'/source_file) == expected
assert digest(generated/'src/sparse_flash_attention'/source_file) == expected
assert not (root/'runtime_candidate_a2').exists()
shutil.copytree(root/'runtime_baseline',root/'runtime_candidate_a2')
destination = Path('vllm_ascend/_cann_ops_custom/vendors/custom_transformer/op_impl/ai_core/tbe/kernel/ascend910b/sparse_flash_attention')
files = sorted((generated/'bin/sparse_flash_attention').glob('*'))
assert len([p for p in files if p.suffix=='.o']) == 2
record = dict(source_sha256=expected,baseline={},candidate={},shared_libraries={})
for p in files:
    target = root/'runtime_candidate_a2'/destination/p.name
    baseline = root/'runtime_baseline'/destination/p.name
    assert baseline.exists()
    record['baseline'][p.name] = digest(baseline)
    shutil.copy2(p,target)
    record['candidate'][p.name] = digest(target)
    if p.suffix=='.o':
        assert digest(target)!=digest(baseline)
for p in (root/'runtime_baseline/vllm_ascend').glob('*.so'):
    assert digest(p)==digest(root/'runtime_candidate_a2/vllm_ascend'/p.name)
    record['shared_libraries'][p.name]=digest(p)
(root/'iteration-a2/kernel-hashes.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
