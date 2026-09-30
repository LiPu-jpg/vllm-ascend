"""Actual decoder methods and operators; no mocked registration or loader.

This checks mHC method integration and is not full model/checkpoint accuracy.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import torch
import torch_npu
from torch import nn
from vllm_ascend.utils import enable_custom_op
from vllm_ascend.models.glm5next.model import Glm5NextDecoderLayer


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',type=Path)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    assert enable_custom_op()
    torch_npu.npu.config.allow_internal_format=True
    torch.set_num_threads(1)
    path=Path('/mnt/workspace/hc-pre-reduction-20260930/iteration-03/test_npu_hc_pre_v2.py')
    spec=importlib.util.spec_from_file_location('original_oracle',path)
    oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    rows=[]
    with torch.inference_mode():
        for hidden in (4096,7168):
            for tokens in (1,17,129):
                for signed in (False,True):
                    for norm in (False,True):
                        index=len(rows);iters=(1,3,20)[index%3]
                        scale=2.0 if index%2==0 else 1.5
                        key=f't{tokens}-d{hidden}-signed{int(signed)}-norm{int(norm)}-i{iters}-p{scale}'
                        layer=Glm5NextDecoderLayer.__new__(Glm5NextDecoderLayer)
                        nn.Module.__init__(layer)
                        layer.n=4;layer.mhc_sinkhorn_iterations=iters
                        layer.rms_norm_eps=1e-6;layer.hc_eps=1e-6;layer.mhc_post_mult_value=scale
                        x,fn,sc,base=oracle._make_hc_pre_inputs((tokens,4,hidden))
                        if signed:
                            x=(x.float()-1).bfloat16();fn=fn-0.5/(4*hidden);base=torch.linspace(-3,3,24)
                        weight=torch.linspace(0.5,1.5,hidden).bfloat16().npu() if norm else None
                        inputs=tuple(v.npu() for v in (x,fn,sc,base));original=inputs[0].clone()
                        def call():
                            first=layer.hc_pre(*inputs,norm_weight=weight,norm_eps=1e-5)
                            chain=layer.hc_post_pre(first[2],inputs[0],first[0],first[1],*inputs[1:],norm_weight=weight,norm_eps=1e-5)
                            return (*first,*chain)
                        actual=call();torch.npu.synchronize()
                        graph=torch.npu.NPUGraph()
                        with torch.npu.graph(graph):
                            captured=call()
                        graph.replay();torch.npu.synchronize()
                        row={'case':key,'errors':[],'mode':'eager+graph','cpu_checks':[]}
                        for i,(a,b) in enumerate(zip(actual,captured,strict=True)):
                            if not torch.equal(a.view(torch.uint8),b.view(torch.uint8)):
                                row['errors'].append(f'graph parity output {i}')
                        if not torch.equal(inputs[0],original):row['errors'].append('input changed')
                        checks=[]
                        for stage,values,source in [('pre',actual[:3],x),('post_pre',actual[4:],actual[3].cpu())]:
                            y,post,comb,_=oracle._hc_pre_cpu(source,fn,sc,base,sinkhorn_iters=iters)
                            post=post.mul(scale/2).unsqueeze(-1)
                            if norm:
                                yf=y.float();w=weight.cpu().float()
                                y=(yf*torch.rsqrt(yf.square().mean(-1,keepdim=True)+1e-5)*w).bfloat16()
                            for i,(a,b) in enumerate(zip(values,(post,comb,y),strict=True)):
                                try:
                                    oracle._assert_close_with_pass_rate(a,b,diff_threshold=oracle.Y_DIFF_THRESHOLD if i==2 else oracle.AUX_DIFF_THRESHOLD,required_pass_rate=oracle.Y_REQUIRED_PASS_RATE if i==2 else oracle.AUX_REQUIRED_PASS_RATE)
                                    row['cpu_checks'].append(f'{stage}:{i}:pass')
                                except AssertionError as error:row['errors'].append(f'{stage}:{i}:{error}')
                        cpu=tuple(v.cpu() for v in actual)
                        if args.reference:
                            ref=torch.load(args.reference/f'{key}.pt',weights_only=True)
                            for i,(a,b) in enumerate(zip(cpu,ref,strict=True)):
                                if not torch.equal(a.view(torch.uint8),b.view(torch.uint8)):row['errors'].append(f'baseline parity {i}')
                        destination=args.output/f'{key}.pt';torch.save(cpu,destination)
                        row['sha256']=hashlib.sha256(destination.read_bytes()).hexdigest()
                        rows.append(row);(args.output/'results.json').write_text(json.dumps(rows,indent=2))
                        print(key,'PASS' if not row['errors'] else row['errors'],flush=True)
                        del graph
    (args.output/'loaded-libraries.txt').write_text('\n'.join(s for s in Path('/proc/self/maps').read_text().splitlines() if 'libcust_' in s or 'vllm_ascend_C' in s))
    failures=sum(bool(row['errors']) for row in rows)
    print('DECODER_METHOD_RESULTS',len(rows),failures,flush=True)
    raise SystemExit(bool(failures))

if __name__=='__main__':main()
