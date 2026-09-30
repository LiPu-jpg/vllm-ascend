### What this PR does / why we need it?

HcPre is called by the GLM-5.3-Flash and DeepSeek mHC layers, but its nightly numerical coverage fixes Sinkhorn at 20 iterations and primarily uses small, nonnegative inputs. Add 48 cases covering iteration counts 1/3/20, hidden sizes 4096/7168, 1/17/257 tokens and a 3x17 batch, signed cancellation inputs, repeatability and input preservation. The five original cases and their accuracy thresholds remain unchanged; the CPU reference still defaults to 20 iterations.

Add `benchmarks/hc_pre.py` and documentation for complete-operator eager/ACL-graph measurements. Retain every warmup/sample, check all four outputs byte for byte against a saved reference, and report graph measurements per operator with capture/setup excluded. Measure projection, gates, Sinkhorn and stream contraction together. Scalar attributes are passed by keyword, as required by the production Torch schema.

No operator, tiling, model, dispatch or environment-variable implementation changes are included. Source/overlap checks found the existing fused integration (#16321), removed unused standalone Sinkhorn (#12896) and active batch optimization (#17054). No competition source was imported or relicensed.

### Does this PR introduce _any_ user-facing change?

No inference behavior changes. Developers gain numerical coverage and a reproducible full-HcPre benchmark. This PR makes no operator or full-model acceleration claim.

### How was this patch tested?

- `bash format.sh ci` and `git diff --check` passed on source revision `52c8d05cba1b3b40999dbe473030ed3d29045561`. All source and evidence commits include DCO Signed-off-by trailers.
- Ascend 910B3 (physical NPU 3, logical NPU 0), CANN 9.1.0, torch 2.10.0+cpu / torch_npu 2.10.0.post4, Python 3.12. Shared environments were reused without modification. Private OPP packages use identical build flags and separate vendors. Each launch checked for an idle NPU.
- **53/53 tests passed through the real full-plugin loader**, using the unchanged PR test file with `--confcutdir` at `singlecard_ops`. No test body, CPU oracle, operator registration or loader function was replaced. The isolated PR Python checkout reused a complete existing extension; its HcPre binding section was checked byte for byte against this PR's source, and binary/source hashes and actual module/library paths are retained. This is not a fresh full-project build from the PR revision.
- The real-plugin benchmark completed **all 28 positive/strong-signed cases** in eager and graph modes, three rounds of 20 warmups + 50 samples. All four eager outputs matched the earlier unchanged baseline byte for byte; graph outputs matched eager; inputs were preserved. The runner only invokes the original entrypoints and records import/library paths at exit.
- Real-plugin validation exposed an initial benchmark failure: four scalar arguments were incorrectly passed positionally. The standalone harness registered those arguments as positional-or-keyword, whereas production makes them keyword-only. The call is fixed; the original failure and schema declaration are retained. The earlier harness used unchanged C++ allocation/checking/ACLNN functions but did not exactly reproduce the production Torch registration.
- A proposed accumulator-copy optimization remains **excluded**. Original standalone graph ABBA: 11/28 faster, 17/28 slower, geometric mean speedup 1.00351. Additional full-plugin graph ABBA: 24/28 faster, 4/28 slower, geometric mean 1.04412, maximum slowdown 3.03%. The materially different execution setups are reported separately; neither is selectively substituted or presented as a stable optimization or model speedup. Every case, slowdown, six round medians per arm and all samples are retained. Unrelated host-side FLA compilation continued; no unrelated NPU process was observed in the saved guards.
- Initial stronger signed-input CPU-oracle testing yielded **14 pass / 7 fail on the unchanged baseline**. Exact fixtures and failures remain public; no threshold was widened. Accepted signed numerical fixtures retain the existing `1/fan_in` weight scale. Stronger benchmark fixtures establish baseline parity, not CPU accuracy.

Subsequent validation after the existing FLA build completed: **normal nightly collection (without `--confcutdir`) passed all 53 cases**, and the related GLM mHC UT passed 4 cases. No stub, test-body change or loader replacement was used. The original dependency/collection failures remain retained. The UT mocks operators by its upstream design and is not a real NPU decoder/model integration result.

A separate runtime candidate [d50abbec](https://github.com/LiPu-jpg/vllm-ascend/commit/d50abbec269b1f55983f122388d608b0fab38a62) peels the first FP32 reduction addition to avoid its initializer copy and an inner-loop accumulator-selection condition. It preserves single-row/padded copying and the FP32 left fold. Its private NPU kernel built successfully and passed the same 53 normal nightly cases; source `format.sh ci` passed. **This candidate is not included in this PR**, and has no accepted stable performance or model result yet. L1 diagnostics of the original candidate show reduced vector work but increased scalar work at the largest inspected case; graph kernel counters are available while ACL-to-NPU flow association is incomplete. TASK_QUEUE_ENABLE defaults to 1, so an unset earlier value does not establish a cause for the historical discrepancy.

Subsequent exact-source validation built the complete native extension and direct kernels from runtime commit `d50abbec269b1f55983f122388d608b0fab38a62` using the official root CMake build. Normal nightly again passed **53/53**. Actual GLM decoder-method validation passed **24/24 per variant**, including eager/graph and baseline byte parity. Three diagnostic processes observed the actual variant-specific HcPre `.o` file opens and verified their hashes; these diagnostics use LD_PRELOAD, while timing does not.

The **standard vLLM DummyModelLoader** four-layer BF16 GLM smoke passed for baseline and candidate in eager and FULL_DECODE_ONLY configurations. Each arm generated 32 tokens for four requests, with 160 finite logprobs; all token IDs and logprobs are exactly equal (maximum difference 0). Both arms use the identical independent packed-convolution prerequisite from #17828 (`cbb707903e619db01439e19731b0e688377326fe`, wrapper file only) in a private checkout. The unpatched baseline's nonfinite multi-request failure is retained. No bounded/custom loader, operator substitute, dependency stub or registration replacement is used. This is synthetic functional integration, not trained-checkpoint accuracy or model throughput. Runtime graph execution is now confirmed by both model traces: each has 14 aclmdlRIExecuteAsync events and 112 HcPre kernels with captured graph model IDs, plus 24 eager HcPre kernels.

**Draft performance limits:** long-warmup same-kernel A/A still shows measurement variation (geometric mean 0.98566, maximum apparent slowdown 3.78%). The separate runtime candidate gives provisional ABBA 1.01638, 22/28 faster and 6/28 slower, maximum slowdown 4.30%; all cases, six round medians and raw samples remain retained. These gains are not accepted as stable performance evidence. One earlier ABBA is explicitly invalidated by concurrent NPU work. Subsequent queued-replay controls and profiling reject the reduction candidate, as detailed below. A3/A5 hardware remains unverified. This PR still includes no runtime optimization.

[Immutable iteration-02 evidence: complete extension build, kernel-open hashes, all timing controls, retained failures and standard-loader model parity](https://github.com/LiPu-jpg/vllm-ascend/tree/6e617ccfe0ede994cfe25d99468f0a5df36fe2d7/contribution-evidence-hc-pre-20260930/runtime-iteration-02).

[Runtime iteration evidence, normal nightly XML/logs, all diagnostic counters and retained scheduling failures](https://github.com/LiPu-jpg/vllm-ascend/tree/d25762d21db283ce18b040576fdd771153f581f5/contribution-evidence-hc-pre-20260930/runtime-iteration-01).

[Complete immutable evidence](https://github.com/LiPu-jpg/vllm-ascend/tree/00cfe4fa87b88a51ae3dc5a59a827e5191c7fbfa/contribution-evidence-hc-pre-20260930), [real-plugin validation and retained failures](https://github.com/LiPu-jpg/vllm-ascend/tree/00cfe4fa87b88a51ae3dc5a59a827e5191c7fbfa/contribution-evidence-hc-pre-20260930/full-validation), [all-case full-plugin comparison](https://github.com/LiPu-jpg/vllm-ascend/tree/00cfe4fa87b88a51ae3dc5a59a827e5191c7fbfa/contribution-evidence-hc-pre-20260930/full-validation/comparison.md), and [source/license audit](https://github.com/LiPu-jpg/vllm-ascend/tree/00cfe4fa87b88a51ae3dc5a59a827e5191c7fbfa/contribution-evidence-hc-pre-20260930/source-audit.md).

Reproduction in a complete supported environment:

```shell
pytest -sv tests/e2e/nightly/single_node/ops/singlecard_ops/test_npu_hc_pre.py
python benchmarks/hc_pre.py --label baseline-a --output results/baseline-a --timing graph
# Install the comparison revision in its own environment, retaining toolkit and inputs.
python benchmarks/hc_pre.py --label candidate-a --output results/candidate-a \
    --reference results/baseline-a --timing graph
```

For the exact successful isolated collection, add `--confcutdir=tests/e2e/nightly/single_node/ops/singlecard_ops`. The immutable evidence contains the complete scripts, paths, package/source hashes, XML and raw data.

**Completed runtime investigation: the first-add reduction is rejected.** Queued A/A is 0.99941293 geometric mean, with remaining per-case variation. Candidate ABBA is 0.98385720, 16/28 faster and 12/28 slower, maximum slowdown 8.45%; independent pairs reproduce several small-batch regressions. Matched original-candidate production/probe controls give 1.00187839/1.00848297, both 16 faster and 12 slower. These do not reproduce the historical fixed production advantage. An event submission gap and measurement variability are observed, but the exact historical cause is not proved; the old 1.04412 result is not accepted optimization evidence.

All 42 new L1 operator cases and both actual model traces are retained. Slow small-batch cases also show increased kernel duration and AIV scalar duration; the installed disassembler cannot decode the ISA, so a specific instruction cause remains unproved. Baseline and candidate initially pass 93/120 tail CPU cases; candidate has 12 cross-process parity failures at hidden=7169. A later identical-baseline A/A passes 117/120 but differs in all 24 hidden=7169 cases. Baseline tail instability is established under these conditions; it does not establish candidate correctness or convert failed CPU cases into passes.

[Immutable complete diagnostic evidence, all raw samples, failures, 42 operator profiles and actual model graph traces](https://github.com/LiPu-jpg/vllm-ascend/tree/2d54041acaedc41ed224d416e9e7bb34983ecfec/contribution-evidence-hc-pre-20260930/runtime-iteration-02).

A separate [optional-output V2 runtime candidate](https://github.com/LiPu-jpg/vllm-ascend/commit/5fdc629) omits the unused `pre` allocation and uses the kernel's existing optional-output contract, while retaining V3's four outputs. It is not included in this test PR. Matched V2 performance, tail diagnostics, caller/model verification and profiling are under investigation; no speedup is claimed.

- vLLM main: https://github.com/vllm-project/vllm/commit/ced6857afa0ea7b2e3f0846a62e1394e90f15607

