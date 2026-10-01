"""Limited NoPE numerical smoke before the complete test/performance matrices."""

import argparse
import json
import math
from pathlib import Path

import paired
import test_helper as test
import torch
import torch_npu  # noqa: F401
from experiment import guard


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=["baseline", "candidate"], required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert test.enable_custom_op()
    rows = []
    for label in ["native-torch.float16-1", "native-torch.bfloat16-1"]:
        guard()
        cpu = torch.load(args.captures / f"{label}-inputs.pt", weights_only=True)
        cpu["query_rope"] = cpu["key_rope"] = None
        key = cpu["key"][cpu["block_table"][0].long(), :, 0].reshape(-1, 512).double()
        indices = cpu["sparse_indices"][0, 0].long()
        indices = indices[(indices >= 0) & (indices < int(cpu["actual_seq_lengths_kv"][0]))]
        scores = cpu["query"][0].double() @ key[indices].T / math.sqrt(512)
        expected = scores.softmax(-1) @ key[indices]
        expected_lse = scores.logsumexp(-1)
        inputs = {name: value.npu() if isinstance(value, torch.Tensor) else value for name, value in cpu.items()}
        for return_lse in [False, True]:
            result = torch.ops._C_ascend.npu_sparse_flash_attention(
                **inputs,
                scale_value=1 / math.sqrt(512),
                sparse_block_size=1,
                layout_query="TND",
                layout_kv="PA_BSND",
                sparse_mode=3,
                attention_mode=2,
                return_softmax_lse=return_lse,
            )
            torch.testing.assert_close(result[0].cpu().double()[0], expected, atol=0.03, rtol=0.01)
            if return_lse:
                lse = (result[1].cpu().double() + result[2].cpu().double().log()).reshape(-1)
                torch.testing.assert_close(lse, expected_lse, atol=0.005, rtol=0.001)
            rows.append(
                dict(case=label, return_lse=return_lse, status="passed", input_sha256=paired.digest_inputs(cpu))
            )
            args.output.write_text(json.dumps(dict(complete=False, rows=rows), indent=2) + "\n")
    guard()
    args.output.write_text(json.dumps(dict(complete=True, rows=rows), indent=2) + "\n")


if __name__ == "__main__":
    main()
