"""Production HcPre tail diagnostics using the unchanged upstream CPU oracle."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import torch
import torch_npu
from vllm_ascend.utils import enable_custom_op


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reference',type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    assert enable_custom_op()
    torch_npu.npu.config.allow_internal_format=True;torch.set_num_threads(1)
    path=args.repo/'tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py'
    spec=importlib.util.spec_from_file_location('upstream_oracle',path)
    oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
    rows=[]
    with torch.inference_mode():
        for hidden in (8,64,4103,4104,7169):
            for tokens in (1,17):
                for signed in (False,True):
                    for iters in (1,3,20):
                        for external in (False,True):
                            key=f't{tokens}-d{hidden}-signed{int(signed)}-i{iters}-external{int(external)}'
                            row={'case':key,'cpu_accuracy_pass':False,'errors':[]}
                            x,fn,scale,base=oracle._make_hc_pre_inputs((tokens,4,hidden))
                            if signed:
                                x=(x.float()-1).bfloat16();fn=fn-0.5/(4*hidden);base=torch.linspace(-3,3,24)
                            mix=torch.linspace(-0.2,1.2,tokens*4).reshape(tokens,4) if external else None
                            expected=oracle._hc_pre_cpu(x,fn,scale,base,pre_mix=mix,sinkhorn_iters=iters)
                            inputs=tuple(t.npu() for t in (x,fn,scale,base))
                            device_mix=mix.npu() if external else None
                            original=tuple(t.clone() for t in inputs)
                            def call():
                                return torch.ops._C_ascend.npu_hc_pre_v3(*inputs,device_mix,hc_mult=4,hc_sinkhorn_iters=iters,norm_eps=1e-6,hc_eps=1e-6)
                            try:
                                actual=call();repeat=call();torch.npu.synchronize()
                                cpu=tuple(t.cpu() for t in actual)
                                cpu_errors=[]
                                for i,(a,b) in enumerate(zip(actual,expected,strict=True)):
                                    try:
                                        oracle._assert_close_with_pass_rate(a,b,diff_threshold=oracle.Y_DIFF_THRESHOLD if i==0 else oracle.AUX_DIFF_THRESHOLD,required_pass_rate=oracle.Y_REQUIRED_PASS_RATE if i==0 else oracle.AUX_REQUIRED_PASS_RATE)
                                    except AssertionError as error:cpu_errors.append(f'{i}:{error}')
                                row['cpu_errors']=cpu_errors;row['cpu_accuracy_pass']=not cpu_errors
                                for i,(a,b) in enumerate(zip(actual,repeat,strict=True)):
                                    if not torch.equal(a.view(torch.uint8),b.view(torch.uint8)):row['errors'].append(f'repeat:{i}')
                                graph=torch.npu.NPUGraph()
                                with torch.npu.graph(graph):captured=call()
                                graph.replay();torch.npu.synchronize()
                                for i,(a,b) in enumerate(zip(actual,captured,strict=True)):
                                    if not torch.equal(a.view(torch.uint8),b.view(torch.uint8)):row['errors'].append(f'graph:{i}')
                                del graph
                                for a,b in zip(inputs,original,strict=True):
                                    if not torch.equal(a,b):row['errors'].append('input changed')
                                if args.reference:
                                    ref=torch.load(args.reference/f'{key}.pt',weights_only=True)
                                    for i,(a,b) in enumerate(zip(cpu,ref,strict=True)):
                                        if not torch.equal(a.view(torch.uint8),b.view(torch.uint8)):row['errors'].append(f'baseline parity:{i}')
                                destination=args.output/f'{key}.pt';torch.save(cpu,destination)
                                row['sha256']=hashlib.sha256(destination.read_bytes()).hexdigest()
                            except Exception as error:
                                row['errors'].append(f'{type(error).__name__}:{error}')
                            rows.append(row);(args.output/'results.json').write_text(json.dumps(rows,indent=2))
                            print(key,row,flush=True)
    print('BOUNDARY_COUNTS',len(rows),'cpu_pass',sum(r['cpu_accuracy_pass'] for r in rows),'other_fail',sum(bool(r['errors']) for r in rows),flush=True)
    # A baseline CPU failure is preserved as a failure; parity never overrides it.
    raise SystemExit(any(not r['cpu_accuracy_pass'] or r['errors'] for r in rows))

if __name__=='__main__':main()
