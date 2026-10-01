"""Actual DCP index-remap -> device-dispatch component check on one receiver.
This does not run a distributed group, query gather, output merge, or model.
"""
import argparse, hashlib, inspect, itertools, json
from pathlib import Path
from types import SimpleNamespace
import torch
import torch_npu
from experiment import guard
from test_helper import _make_inputs, _check
from vllm_ascend.utils import enable_custom_op
import vllm_ascend.ops
from vllm_ascend.device.device_op import BaseDeviceAdaptor
from vllm_ascend.attention.context_parallel.sfa_cp import AscendSFADCPImpl, HAS_TRITON

@torch.inference_mode()
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--variant',choices=('baseline','candidate'),required=True)
 parser.add_argument('--output',type=Path,required=True)
 parser.add_argument('--reference',type=Path,required=True)
 args=parser.parse_args(); args.reference.mkdir(parents=True,exist_ok=True)
 assert enable_custom_op()
 rows=[]
 for index,(dtype,rank,interleave,count) in enumerate(itertools.product((torch.float16,torch.bfloat16),(0,7),(1,16),(1,127,257,513,2048))):
  guard()
  inputs,expected,lse=_make_inputs(dtype,64,[1],[4096],[count],4096)
  expected_local=inputs['sparse_indices'].cpu()
  local=expected_local[0,0,:count].long()
  own_global=(local//interleave*8+rank)*interleave+local%interleave
  other_local=torch.randperm(4096)[:2048-count].long()
  other_global=(other_local//interleave*8+(rank+1)%8)*interleave+other_local%interleave
  global_indices=torch.cat((own_global,other_global)).sort().values.int().reshape(1,1,2048).npu()
  receiver=SimpleNamespace(dcp_size=8,dcp_rank=rank,_dcp_interleave_size=interleave,
   _dcp_index_topk=2048,_remap_order=torch.arange(2048,dtype=torch.float32,device='npu'),
   _remap_invalid_index=torch.tensor(-1,dtype=torch.float32,device='npu'))
  remapped=AscendSFADCPImpl._remap_sparse_indices(receiver,global_indices)
  torch.testing.assert_close(remapped.cpu(),expected_local,rtol=0,atol=0)
  for mode in (0,3):
   result=BaseDeviceAdaptor.execute_sparse_flash_attention_process(SimpleNamespace(scale=1/24),
    inputs['query'],inputs['query_rope'],(inputs['key'],inputs['key_rope']),remapped,
    SimpleNamespace(block_table=inputs['block_table']),inputs['actual_seq_lengths_query'],
    inputs['actual_seq_lengths_kv'],sparse_mode=mode,return_lse=True)
   _check(result,expected,lse)
   actual=[x.cpu() for x in result]; path=args.reference/f'{index}-{mode}.pt'
   if args.variant=='baseline':
    if path.exists():
     saved=torch.load(path,weights_only=True)
     assert all(torch.equal(x.contiguous().view(torch.uint8),y.contiguous().view(torch.uint8)) for x,y in zip(actual,saved,strict=True))
    else:torch.save(actual,path)
   same=None
   if args.variant=='candidate':
    same=[torch.equal(x.contiguous().view(torch.uint8),y.contiguous().view(torch.uint8))
     for x,y in zip(actual,torch.load(path,weights_only=True),strict=True)]
    assert all(same)
   guard()
   rows.append(dict(index=index,dtype=str(dtype),rank=rank,interleave=interleave,
    local_count=count,global_topk=2048,sparse_mode=mode,remap_exact=True,reference='passed',
    bytewise_baseline_by_output=same))
   print(json.dumps(rows[-1]),flush=True)
   args.output.write_text(json.dumps(dict(complete=False,rows=rows),indent=2)+'\n')
 metadata=dict(scope='single DCP receiver component; no distributed communication or model',
  remap_backend='triton' if HAS_TRITON else 'torch fallback',
  remap_sha256=hashlib.sha256(inspect.getsource(AscendSFADCPImpl._remap_sparse_indices).encode()).hexdigest(),
  dispatch_sha256=hashlib.sha256(inspect.getsource(BaseDeviceAdaptor.execute_sparse_flash_attention_process).encode()).hexdigest(),
  module_path=inspect.getfile(AscendSFADCPImpl))
 args.output.write_text(json.dumps(dict(complete=True,metadata=metadata,rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
