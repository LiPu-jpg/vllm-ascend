"""Alias physical pages to check large logical offsets without huge KV storage.

Keep every original reference failure or unsupported case visible. Candidates
must match successfully captured original outputs byte-for-byte.
"""

import argparse
import hashlib
import json
from pathlib import Path

import torch
import torch_npu  # noqa: F401
import vllm_ascend

from experiment import guard
from paired import digest_inputs
import test_helper as test


@torch.inference_mode()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--variant',choices=('baseline','candidate'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    args.reference.mkdir(exist_ok=True,parents=True)
    assert test.enable_custom_op()
    rows=[]
    meta=dict(variant=args.variant,package_path=str(Path(vllm_ascend.__file__).parent),
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    for dtype in (torch.float16,torch.bfloat16):
        for optional_kv in (False,True):
            kv_len=(1<<32)-1024 if optional_kv else (1<<31)-1
            blocks=(2,4) if optional_kv else (1,2,4)
            for block in blocks:
                guard()
                label=f'{dtype}-optional-{optional_kv}-block-{block}'
                path=args.reference/f'{label}.pt'
                if args.variant=='candidate' and not path.exists():
                    rows.append(dict(case=label,status='missing_original_capture'))
                    continue
                torch.manual_seed(1001)
                query=torch.randn(1,64,512,dtype=dtype)
                qr=torch.randn(1,64,64,dtype=dtype)
                key=torch.randn(1,128,1,512,dtype=dtype)
                kr=torch.randn(1,128,1,64,dtype=dtype)
                high=(kv_len-block)//block
                selected=[0,1,high-1,high]
                # The final positive entry is deliberately out of the KV range.
                invalid=min((1<<31)-1,kv_len//block+1)
                if invalid*block<kv_len:invalid=(1<<31)-1
                ids=torch.full((1,1,17),-1,dtype=torch.int32)
                ids[0,0,:5]=torch.tensor(selected+[invalid],dtype=torch.int32)
                table=torch.zeros(1,(kv_len+127)//128,dtype=torch.int32)
                cpu=dict(query=query,key=key,value=key,query_rope=qr,key_rope=kr,
                         sparse_indices=ids,block_table=table,
                         actual_seq_lengths_query=torch.tensor([1],dtype=torch.int32),
                         actual_seq_lengths_kv=None if optional_kv else torch.tensor([kv_len],dtype=torch.int32))
                inputs={k:v.npu() if isinstance(v,torch.Tensor) else v for k,v in cpu.items()}
                inputs['value']=inputs['key']
                error=None
                try:
                    result=torch.ops._C_ascend.npu_sparse_flash_attention(
                        **inputs,scale_value=1/24,sparse_block_size=block,
                        layout_query='TND',layout_kv='PA_BSND',sparse_mode=0,
                        attention_mode=2,return_softmax_lse=True,
                    )
                    actual=[x.cpu() for x in result]
                except RuntimeError as exc:
                    if args.variant=='candidate':raise
                    rows.append(dict(case=label,status='original_execution_failed',error=str(exc)))
                    args.output.write_text(json.dumps(dict(metadata=meta,complete=False,rows=rows),indent=2)+'\n')
                    continue
                logical=(ids[0,0][ids[0,0]>=0].long()[:,None]*block+torch.arange(block)).flatten()
                logical=logical[logical<kv_len]
                physical=logical%128
                logits=(query[0].double()@key[0,physical,0].double().T+qr[0].double()@kr[0,physical,0].double().T)/24
                expected=(logits.softmax(-1)@key[0,physical,0].double()).unsqueeze(0)
                expected_lse=logits.logsumexp(-1).unsqueeze(0)
                try:test._check(result,expected,expected_lse)
                except AssertionError as exc:error=str(exc)
                digest=digest_inputs(inputs)
                if args.variant=='baseline' and not path.exists():
                    torch.save(dict(input_sha256=digest,outputs=actual,reference_passed=error is None),path)
                else:
                    old=torch.load(path,weights_only=True)
                    assert old['input_sha256']==digest
                    assert all(torch.equal(a.contiguous().view(torch.uint8),b.contiguous().view(torch.uint8))
                               for a,b in zip(actual,old['outputs'],strict=True)),label
                    assert old['reference_passed']==(error is None),label
                rows.append(dict(case=label,status='captured' if args.variant=='baseline' else 'byte_parity_passed',
                                 input_sha256=digest,reference_passed=error is None,reference_error=error,
                                 max_valid_logical_token=int(logical.max()),block_table_bytes=table.numel()*4))
                args.output.write_text(json.dumps(dict(metadata=meta,complete=False,rows=rows),indent=2)+'\n')
                del inputs,cpu,result,actual,table,key,kr,query,qr
    guard()
    args.output.write_text(json.dumps(dict(metadata=meta,complete=True,rows=rows),indent=2)+'\n')


if __name__=='__main__':
    main()
