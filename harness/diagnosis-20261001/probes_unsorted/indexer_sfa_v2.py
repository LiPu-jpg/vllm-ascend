"""Actual lightning-indexer -> native RoPE64 SFA component captures.

Baseline captures actual indexer outputs once. Candidates replay the exact
captured SFA inputs. Score-order and chronological-order cases remain separate.
Random features are synthetic, so this is not a model workload distribution.
"""

import argparse
import hashlib
import json
from pathlib import Path

import torch
import torch_npu
import vllm_ascend

from experiment import guard
from paired import digest_inputs, measure
import test_helper as test


def run_native(inputs):
    return torch.ops._C_ascend.npu_sparse_flash_attention(
        **inputs, scale_value=1/24, sparse_block_size=1,
        layout_query='TND', layout_kv='PA_BSND', sparse_mode=3,
        attention_mode=2, return_softmax_lse=True,
    )


def page_locality(indices):
    hits = transitions = 0
    ascending = 0
    for row in indices.reshape(-1, indices.shape[-1]):
        valid = row[row >= 0].long()
        ascending += int(bool(torch.all(valid[1:] >= valid[:-1])))
        for start in range(0, len(valid), 256):
            pages = valid[start:start+256] // 128
            hits += int((pages[1:] == pages[:-1]).sum())
            transitions += max(len(pages)-1, 0)
    return dict(adjacent_page_hits=hits, adjacent_transitions=transitions,
                page_hit_rate=hits/transitions if transitions else None,
                ascending_rows=ascending, total_rows=indices.shape[0])


def golden(inputs):
    q = inputs['query'].double()
    qr = inputs['query_rope'].double()
    table = inputs['block_table'].long()[0]
    key = inputs['key'][table, :, 0].reshape(-1, 512).double()
    rope = inputs['key_rope'][table, :, 0].reshape(-1, 64).double()
    ids = inputs['sparse_indices'][:, 0].long()
    kv_len = int(inputs['actual_seq_lengths_kv'][0])
    output = torch.zeros_like(q)
    lse = torch.full(q.shape[:2], -torch.inf, dtype=torch.float64)
    for row in range(len(q)):
        visible = kv_len-len(q)+row+1
        selected = ids[row][(ids[row] >= 0) & (ids[row] < visible)]
        if len(selected):
            scores = (q[row] @ key[selected].T + qr[row] @ rope[selected].T)/24
            output[row] = scores.softmax(-1) @ key[selected]
            lse[row] = scores.logsumexp(-1)
    return output, lse


def capture(dtype, query_count, quantized):
    guard()
    inputs, _, _ = test._make_inputs(dtype, 64, [query_count], [4096],
                                    [2048]*query_count, kv_capacity=4096)
    cpu = {name: value.cpu() if isinstance(value, torch.Tensor) else value
           for name, value in inputs.items()}
    torch.manual_seed(1001 + query_count)
    heads = 32
    if quantized:
        query = torch.randint(-32, 32, (query_count, heads, 128), dtype=torch.int8)
        key = torch.randint(-32, 32, (32, 128, 1, 128), dtype=torch.int8)
        weights = torch.rand(query_count, heads, dtype=torch.float16)
        q_scale = torch.rand(query_count, heads, dtype=torch.float16)/32
        k_scale = torch.rand(32, 128, 1, dtype=torch.float16)/32
        indices = torch.ops._C_ascend.npu_lightning_indexer_quant(
            query=query.npu(), key=key.npu(), weights=weights.npu(),
            query_dequant_scale=q_scale.npu(), key_dequant_scale=k_scale.npu(),
            actual_seq_lengths_query=inputs['actual_seq_lengths_query'],
            actual_seq_lengths_key=inputs['actual_seq_lengths_kv'], block_table=inputs['block_table'],
            query_quant_mode=0, key_quant_mode=0, layout_query='TND',
            layout_key='PA_BSND', sparse_count=2048, sparse_mode=3,
        )
    else:
        query = torch.randn(query_count, heads, 128, dtype=dtype)
        key = torch.randn(32, 128, 1, 128, dtype=dtype)
        weights = torch.randn(query_count, heads, dtype=dtype)
        indices, _ = torch_npu.npu_lightning_indexer(
            query=query.npu(), key=key.npu(), weights=weights.npu(),
            actual_seq_lengths_query=inputs['actual_seq_lengths_query'],
            actual_seq_lengths_key=inputs['actual_seq_lengths_kv'], block_table=inputs['block_table'],
            layout_query='TND', layout_key='PA_BSND', sparse_count=2048, sparse_mode=3,
        )
    torch.npu.synchronize()
    guard()
    indices = indices.cpu().int().reshape(query_count, 1, 2048)
    for row in range(query_count):
        valid = indices[row][indices[row] >= 0]
        assert valid.numel() == 2048 and valid.unique().numel() == 2048
        assert int(valid.max()) < 4096-query_count+row+1
    cpu['sparse_indices'] = indices
    return cpu


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variant', choices=('baseline', 'candidate'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    args.reference.mkdir(parents=True, exist_ok=True)
    assert test.enable_custom_op()
    # Use the existing paired measurement's exact schedule with mode3 native SFA.
    test._run = run_native
    rows = []
    metadata = dict(variant=args.variant, device=torch.npu.get_device_name(0),
                    package_path=str(Path(vllm_ascend.__file__).parent),
                    torch_version=torch.__version__, torch_npu_version=torch_npu.__version__,
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    paired_sha256=hashlib.sha256(Path(__file__).with_name('paired.py').read_bytes()).hexdigest())
    for quantized in (False, True):
        for dtype in (torch.float16, torch.bfloat16):
            for query_count in (1, 32):
                guard()
                label=f'{"quant" if quantized else "native"}-{dtype}-{query_count}'
                capture_path=args.reference/f'{label}-inputs.pt'
                if args.variant == 'baseline' and not capture_path.exists():
                    try:
                        cpu = capture(dtype, query_count, quantized)
                    except Exception as exc:
                        # Preserve unsupported/error cases explicitly, never silently drop.
                        rows.append(dict(case=label,status='capture_failed',error=repr(exc)))
                        args.output.write_text(json.dumps(dict(metadata=metadata,complete=False,rows=rows),indent=2)+'\n')
                        continue
                    torch.save(cpu,capture_path)
                else:
                    if not capture_path.exists():
                        rows.append(dict(case=label,status='missing_baseline_capture'))
                        continue
                    cpu = torch.load(capture_path,weights_only=True)
                for order in ('indexer', 'chronological'):
                    guard()
                    ordered = dict(cpu)
                    if order == 'chronological':
                        indices = cpu['sparse_indices'].clone()
                        for row in indices[:,0]:
                            valid=row[row>=0].sort().values
                            row.fill_(-1)
                            row[:len(valid)]=valid
                        ordered['sparse_indices']=indices
                    expected,lse=golden(ordered)
                    inputs={name:value.npu() if isinstance(value,torch.Tensor) else value
                            for name,value in ordered.items()}
                    result=run_native(inputs)
                    checks=test._check(result,expected,lse)
                    actual=[x.cpu() for x in result]
                    digest=digest_inputs(inputs)
                    path=args.reference/f'{label}-{order}-outputs.pt'
                    if args.variant=='baseline' and not path.exists():
                        torch.save(dict(input_sha256=digest,outputs=actual),path)
                    else:
                        previous=torch.load(path,weights_only=True)
                        assert previous['input_sha256']==digest
                        assert all(torch.equal(x.view(torch.uint8),y.view(torch.uint8))
                                   for x,y in zip(actual,previous['outputs'],strict=True))
                    device,wall=measure(inputs)
                    rows.append(dict(case=label,order=order,status='passed',input_sha256=digest,
                                     locality=page_locality(ordered['sparse_indices']),
                                     graph_device_us=device,eager_batch_wall_us=wall,**checks))
                    args.output.write_text(json.dumps(dict(metadata=metadata,complete=False,rows=rows),indent=2)+'\n')
    guard()
    args.output.write_text(json.dumps(dict(metadata=metadata,complete=True,rows=rows),indent=2)+'\n')


if __name__ == '__main__':
    main()
