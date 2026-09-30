### What this PR does / why we need it?

HcPre is called by GLM and DeepSeek mHC layers, but its nightly numerical coverage fixes Sinkhorn at 20 iterations and primarily uses small, nonnegative inputs. Add 48 cases covering finite iteration counts 1/3/20, hidden sizes 4096/7168, token batches 1/17/257 and 3x17, signed cancellation inputs, repeatability and input preservation. Retain the five original cases, CPU-reference default and unchanged accuracy thresholds.

Add a complete-HcPre eager/ACL-graph benchmark and documentation. It retains every warmup/sample, checks all four outputs against a saved reference, excludes graph capture/setup and passes scalar attributes by keyword to match the production Torch schema.

This draft contains **tests, benchmark and documentation only**. No kernel, tiling, dispatch or model implementation change is included. The intended inference optimization remains unfinished: the tested runtime candidates below have not established stable latency gains. No competition source was imported or relicensed.

### Does this PR introduce _any_ user-facing change?

No inference behavior changes and no operator or model speedup claim.

### How was this patch tested?

- Source `52c8d05cba1b3b40999dbe473030ed3d29045561`: `bash format.sh ci` passed; DCO Signed-off-by commits.
- Normal nightly collection passes **53/53** through the full plugin, without `--confcutdir`, dependency stubs or loader replacement. Earlier isolated collection and dependency failures remain in the evidence.
- Complete-plugin benchmark covers all 28 positive/signed cases in eager and graph modes, with retained raw samples and byte parity. The original positional-argument failure and the corrected keyword-only production call are retained.
- Ascend 910B3 physical NPU 3/logical 0, CANN 9.1.0, torch 2.10.0+cpu, torch_npu 2.10.0.post4 and vLLM `ced6857afa0ea7b2e3f0846a62e1394e90f15607`. Private sources/OPP packages reuse the existing environment; guards record NPU and foreign jobs before/after each process.

### Runtime investigation: excluded candidates

| Candidate | Complete-operator result | Conclusion |
| --- | --- | --- |
| First-add FP32 reduction | Queued graph ABBA 0.98385720 geometric mean speedup; 16 faster / 12 slower; max slowdown 8.45% | Rejected |
| Skip unused V2 `pre` output | Graph ABBA 1.026566 versus BAAB 1.005557 and A/A 1.008365; eager ABBA 0.998681, same-code eager A/A 1.106062 | Allocation reduction proven; stable latency gain unproved |
| Contiguous Cast | Graph ABBA 0.978565531 (4 faster / 24 slower, max slowdown 7.54%); BAAB 0.994634162 (9 / 19, max slowdown 4.21%); eager independent pairs disagree | Rejected |

Each candidate uses real full-plugin registration, independent processes, identical inputs/build flags/configuration and retained ABBA/A/A controls. Profiler measurements remain diagnostic and are not pooled into benchmark samples. A/A variation is not subtracted to manufacture a gain. Actual kernel file-open paths and object hashes are recorded separately using instrumentation absent from timing.

The later optional-output and Cast cohorts each pass 41/41 normal nightly cases and 24/24 actual GLM decoder-method checks per arm. These are separate candidate suites, not a replacement claim about this PR's 53-case suite. Cast caller serialized output hashes match across arms.

Standard DummyModelLoader four-layer BF16 GLM eager and graph smoke passes with identical tokens/finite logprobs. Latest Cast model comparison uses eight requests, 64 tokens and 320 logprobs per arm, maximum difference 0. Actual traces prove 14 aclmdlRIExecuteAsync events, 112 graph HcPre kernels and 24 eager kernels per arm. Both arms use the same independent packed-convolution prerequisite from #17828 in private sources. This proves synthetic functional integration, not checkpoint accuracy or model throughput.

Known boundary failures remain explicit: later 60-case suites pass 45 CPU cases per arm, with six candidate cross-process parity failures at t1/d7169. Earlier identical-baseline A/A establishes tail instability under those conditions, which does not establish candidate correctness. No threshold is relaxed and no failed boundary case is counted as passed. A3/A5 and final latest-worker integration remain unverified.

The old standalone 1.00351 and full-plugin 1.04412 results do not establish acceleration. Controlled production/probe comparisons do not reproduce a fixed loading-path advantage; event submission gaps and measurement variability are observed, but the unique historical cause is unproved.

[All evidence, including the original source/license audit and failures](https://github.com/LiPu-jpg/vllm-ascend/tree/b6bfe2644fef2f6ff02198b94dbe650f37fdf882/contribution-evidence-hc-pre-20260930), [reduction investigation](https://github.com/LiPu-jpg/vllm-ascend/tree/b6bfe2644fef2f6ff02198b94dbe650f37fdf882/contribution-evidence-hc-pre-20260930/runtime-iteration-02), [optional-output investigation](https://github.com/LiPu-jpg/vllm-ascend/tree/b6bfe2644fef2f6ff02198b94dbe650f37fdf882/contribution-evidence-hc-pre-20260930/runtime-iteration-03), [contiguous Cast: all samples, slowdown cases, builds, profiles and model traces](https://github.com/LiPu-jpg/vllm-ascend/tree/b6bfe2644fef2f6ff02198b94dbe650f37fdf882/contribution-evidence-hc-pre-20260930/runtime-iteration-04). The previous full PR description is also archived, so chronology is not lost.

Reproduce in a complete supported environment:

```shell
pytest -sv tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py
python benchmarks/hc_pre.py --label baseline-a --output results/baseline-a --timing graph
python benchmarks/hc_pre.py --label candidate-a --output results/candidate-a \
    --reference results/baseline-a --timing graph
```

Install comparison revisions independently, keep dependencies and inputs identical, run the full ordered controls and report every result. The evidence contains exact controllers, scripts, refs, commands, XML, hashes and all raw text data. Binary profiler records and tensors remain on the cloud with recorded hashes.

- vLLM main: https://github.com/vllm-project/vllm/commit/ced6857afa0ea7b2e3f0846a62e1394e90f15607

