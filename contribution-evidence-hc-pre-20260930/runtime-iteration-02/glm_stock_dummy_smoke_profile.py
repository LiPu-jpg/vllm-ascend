# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""One-card synthetic GLM smoke, adapted from the project's TP4 fixture.

This retains hidden=4096 and hc_mult=4, but reduces the model to four layers
and eight experts. It is not checkpoint accuracy or production throughput.
Retain the production multimodal wrapper and vision initialization, as in the
upstream fixture, although requests here contain token IDs only.
Run from a complete vllm-ascend installation with this directory on PYTHONPATH.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import torch
from vllm import LLM, SamplingParams
class SmokeWorker:
    def check_model_paths(self):
        from vllm_ascend.models.glm5next.ops import mhc_ops

        modules = list(self.model_runner.model.modules())
        names = [type(module).__name__ for module in modules]
        assert names.count("Glm5NextDecoderLayer") == 4
        assert names.count("Glm5NextLinearAttention") == 3
        assert names.count("Glm5NextMLAAttention") == 1
        assert sum(hasattr(module, "hc_attn_fn") for module in modules) == 4

        def describe_cache(value):
            if isinstance(value, torch.Tensor):
                return {"shape": list(value.shape), "stride": list(value.stride()), "dtype": str(value.dtype)}
            if isinstance(value, (tuple, list)):
                return [describe_cache(item) for item in value]
            return {"type": type(value).__name__}

        return {
            "layers": 4, "kda": 3, "mla": 1, "mhc": 4,
            "expand_impl": f"{mhc_ops.hc_expand.__module__}.{mhc_ops.hc_expand.__name__}",
            "kda_caches": [
                describe_cache(module.kv_cache) for module in modules
                if type(module).__name__ == "Glm5NextLinearAttention"
            ],
            "max_model_len": self.model_runner.max_model_len,
            "max_encoder_len": self.model_runner.max_encoder_len,
        }


def write_model(assets, destination):
    config = json.loads((assets / "config.json").read_text())
    config["num_hidden_layers"] = 4
    config["n_routed_experts"] = 8
    for key in ("layer_types", "mlp_layer_types", "indexer_types"):
        config[key] = config[key][:4]
    config["linear_attn_config"]["kda_layers"] = [0, 1, 2]
    config["linear_attn_config"]["full_attn_layers"] = [3]
    template = json.loads((assets / "quant.json").read_text())
    quant = {
        "model.language_model." + key[len("model."):] if key.startswith("model.") else key: value
        for key, value in template.items() if not key.startswith("model.layers.")
    }
    for layer in range(4):
        source = 0 if layer < 3 else 3
        prefix = f"model.layers.{source}."
        for key, value in template.items():
            if not key.startswith(prefix):
                continue
            target = f"model.language_model.layers.{layer}." + key[len(prefix):]
            if ".experts.0." in target:
                for expert in range(8):
                    quant[target.replace(".experts.0.", f".experts.{expert}.")] = value
            else:
                quant[target] = value
    destination.mkdir(parents=True)
    wrapper = json.loads((assets / "multimodal.json").read_text())
    model_config = {**wrapper, "text_config": {
        key: value for key, value in config.items() if key != "architectures"
    }}
    (destination / "config.json").write_text(json.dumps(model_config, indent=2))
    # Unquantized BF16 fixture uses the standard vLLM dummy loader.
    for name in ("processor_config.json", "tokenizer_config.json", "tokenizer.json"):
        (destination / name).write_bytes((assets / name).read_bytes())
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--graph", action="store_true")
    parser.add_argument("--unused-native", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--inspect-only", action="store_true", help="Inspect model/cache layout without claiming generation success")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    assets = args.repo / "tests/e2e/pull_request/four_card/glm53flash_assets"
    config = write_model(assets, args.output / "model")
    os.environ["VLLM_USE_V2_MODEL_RUNNER"] = "0"
    os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
    os.environ["HCCL_OP_EXPANSION_MODE"] = "AIV"
    os.environ["HCCL_BUFFSIZE"] = "400"
    settings = dict(
        model=str(args.output / "model"),
        load_format="dummy",
        worker_extension_cls=(
            "glm_stock_dummy_smoke.SmokeWorker"
        ),
        skip_tokenizer_init=True,
        dtype="bfloat16",
        tensor_parallel_size=1,
        quantization=None,
        # A 512-token capacity underallocates the existing TP1 hybrid sparse-MLA
        # persistent block-table buffer in this fixture.
        # Keep the same short prompts/batch size, with sufficient table capacity.
        max_model_len=8192,
        max_num_seqs=4,
        max_num_batched_tokens=512,
        limit_mm_per_prompt={"image": 0, "video": 0},
        block_size=128,
        enable_chunked_prefill=True,
        enable_prefix_caching=False,
        gpu_memory_utilization=0.75,
        # Four short requests need only a few recurrent-state pages. Bound this
        # synthetic fixture's pool: the existing NPU index_select path can make
        # a contiguous copy of the entire padded pool before gathering a row.
        kv_cache_memory_bytes=512 * 1024 * 1024,
        seed=1024,
        enforce_eager=not args.graph,
        additional_config={"enable_cpu_binding": False, "enable_fused_mc2": 0},
        profiler_config={
            "profiler": "torch",
            "torch_profiler_dir": str(args.output / "profile"),
            "torch_profiler_with_stack": False,
        },
    )
    if args.graph:
        settings["compilation_config"] = {
            "cudagraph_mode": "FULL_DECODE_ONLY", "cudagraph_capture_sizes": [1, 2, 4]
        }
    model = LLM(**settings)
    paths = model.collective_rpc("check_model_paths")
    expected_impl = (
        "vllm_ascend.models.glm5next.ops.mhc_ops.hc_expand"
    )
    assert all(item["expand_impl"] == expected_impl for item in paths), paths
    print("MODEL_PATHS", paths, flush=True)
    (args.output / "model-paths.json").write_text(json.dumps(paths, indent=2))
    if args.inspect_only:
        print("MODEL_INSPECTION_COMPLETE", flush=True)
        return
    params = SamplingParams(temperature=0, max_tokens=8, ignore_eos=True, detokenize=False, logprobs=5)
    results = []
    for profile in (False, True):
        if profile:
            model.start_profile()
        try:
            for lengths in ((128,), (127, 128, 129)):
                outputs = model.generate(
                    [{"prompt_token_ids": [10 + i % 1000 for i in range(n)]} for n in lengths],
                    params, use_tqdm=False,
                )
                assert len(outputs) == len(lengths)
                for output, prompt_length in zip(outputs, lengths, strict=True):
                    assert output.finished and len(output.outputs) == 1
                    tokens = output.outputs[0].token_ids
                    assert len(tokens) == 8
                    assert all(0 <= token < config["vocab_size"] for token in tokens)
                    logprobs = output.outputs[0].logprobs
                    assert logprobs is not None and len(logprobs) == len(tokens)
                    assert all(math.isfinite(item.logprob) for row in logprobs for item in row.values())
                    results.append({
                        "profiled": profile, "prompt_length": prompt_length, "tokens": list(tokens),
                        "logprobs": [{str(token): item.logprob for token, item in row.items()} for row in logprobs],
                    })
                (args.output / "functional-progress.json").write_text(json.dumps(results, indent=2))
                print("FUNCTIONAL_BATCH_COMPLETE", profile, lengths, flush=True)
        finally:
            if profile:
                model.stop_profile()
    (args.output / "functional-results.json").write_text(json.dumps(results, indent=2))
    print("SYNTHETIC_GLM_SMOKE_PASS", flush=True)


if __name__ == "__main__":
    main()
