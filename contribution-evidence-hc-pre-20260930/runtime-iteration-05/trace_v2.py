"""Resolve actual private kernel file opens in a separate diagnostic process."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op

assert enable_custom_op()
torch_npu.npu.config.allow_internal_format=True
repo=Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-05')
spec=importlib.util.spec_from_file_location('original_benchmark',repo/'hc_pre_v2.py')
benchmark=importlib.util.module_from_spec(spec);spec.loader.exec_module(benchmark)
with torch.inference_mode():
    inputs=benchmark.make_inputs(1,4096,False)
    outputs=torch.ops._C_ascend.npu_hc_pre_v2(*inputs,4,20,1e-6,1e-6)
    torch.npu.synchronize()
    print('FINITE_OUTPUTS',[bool(torch.isfinite(v).all().item()) for v in outputs],flush=True)
trace=Path(os.environ['HC_PRE_FILE_TRACE'])
records=[]
if trace.exists():
    for line in trace.read_text().splitlines():
        operation,fd,name=line.split('\t',2)
        path=Path(name)
        if int(fd)>=0 and path.suffix=='.o' and path.exists():
            records.append({'operation':operation,'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(trace.parent/'opened-kernels.json').write_text(json.dumps(records,indent=2))
print('OPENED_KERNELS',records,flush=True)
if not records:raise SystemExit('No kernel binary open was observed; do not infer selected binary from API library alone')
