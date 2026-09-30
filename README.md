# Nonempty SFA RoPE-padding experiment evidence

**WITHDRAWN after the third candidate (2026-09-30):** this padding optimization is not accepted as a stable upstream performance improvement. Round3 has 11 lower /41 higher device medians across all52 cases, worst slowdown6.84%; its independent profiler has5 lower /47 higher durations. The unchanged-source rebuild is byte-identical to the original baseline. All three candidates and every negative/aborted result remain preserved. [Final rejection report](a3/optimization-summary.md), [round3 all52/ranges/wall data](a3/performance-table.md), [identical-binary process control](a3/build-control-table.md), [regression reassessment](reassessment-20260930/regression-reassessment.md). `a3` denotes iteration3, **not Ascend A3 hardware**. Earlier “final contribution” wording describes the initial draft proposal and is superseded by this withdrawal.

Independent AscendC implementation based on the publicly licensed vllm-ascend kernel/API. No contest source is redistributed or copied. Contest R152, version/score comparison and upstream mechanisms are discussed in optimization-audit.md; the competition score is not an upstream benchmark.

## Scope and provenance

- Project: vllm-project/vllm-ascend; final contribution branch codex/sfa-nonempty-performance-20260930.
- Locked performance baseline source: eee0ef7dfbe99a7ada56dafb3739dd952a0265b5. The 19 SFA sources match the preserved compiled baseline source snapshot; kernel artifact hashes are recorded separately.
- Final integration base: 11682d1e341d161a4129a58863f39a912846f71d. SFA sources/callers and AGENTS.md did not change between the locked integration snapshots.
- A1 experimental commit: a80ee36fc51065fa46ed4b598bea125f5441c434. KEY+RoPE coalescing, larger zero clear. Rejected as final optimization. Source hash 7ea915a66e3bf024a1560b69a92bde8b4743a5aaad03fbdc9271f205b3f540a3.
- A2 experimental commit: 640eb70756f807a22099d643be19eda96bfee6bf. RoPE-only coalescing, original key clear/copies. Source hash 489daf734b639dbd6afb25ed661f250ff4d161e076d55171f4267ce61b749191. The directory name `a2` refers to iteration 2, not a second hardware type.
- Physical device 3, Ascend910B3 (A2), 64 GiB HBM; driver 25.5.0, CANN 9.1.0, Python 3.12.14, PyTorch 2.10.0+cpu and torch_npu 2.10.0.post4. A3 compilation/device validation and whole-model/distributed validation remain outstanding.
- Candidate kernels built with GCC/G++13, Release/O3, `bash build.sh --opkernel --soc=ascend910b --ops=sparse_flash_attention -j2`. Baseline and candidate share identical host/framework libraries; only the two generated SFA kernel objects and their descriptors are installed into private package copies. Source/generated/installed hashes and shared-library hashes are recorded. Shared cloud runtime is not modified.

## Read the results

Unprofiled graph-device and amortized eager-wall timings remain separate from profiler durations. Run order B/C/C/B/B/C uses three fresh processes per variant, five raw samples per case/process, the same 52 fixed **nonempty** cases and matching input hashes. The full table includes NoPE, fully populated tiles, long/short cache, Q1/Q32 and every slowdown. No statistical significance or model throughput gain is claimed. Process variation is preserved.

- `performance-table.md` and `a1/performance-summary.json`: complete rejected A1 results, all 52 cases and raw samples.
- `a2/performance-table.md`: complete independent A2 results. `a2/public-benchmark-table.md` retains additional public-script timings separately; `a2/profiler-comparison.md` retains all52 profiled cases. No A1 result is attributed to A2.
- `profiler-comparison.md` and per-variant `op_statistic.csv`: A1 CPU+NPU, wait=0, warmup=5, active=5, repeat=1; all Total Time(us) rows summed /5. Level1/PipeUtilization is diagnostic, not pooled into the unprofiled benchmark.
- Raw attempt logs and partial JSON preserve detected contention, initial empty-row checking failure, the existing BSND/block8/head1 nonempty LSE NaNs, and test-driver import failures. Expanded reference failures are recorded as failures, not treated as passing numerical accuracy.
- `probes/`: exact measurement, correctness, layout, profiler, input-hash verification and receiver-component scripts, including superseded drivers. They use task-specific paths; adapt paths to your own isolated installations.

A1's 52 cases have 20 lower and 32 higher device medians (maximum reduction 6.91%, maximum slowdown 3.39%). A2's independent comparison has 32 lower and 20 higher device medians (maximum reduction 7.33%, maximum slowdown 3.39%). Four one-selected/Q1/RoPE64 cases improve 5.69–7.33% in pooled A2 medians. Neither iteration shows consistent amortized eager-wall benefit. All regressions remain in the tables.

## Reproduce

Use two isolated package builds at the stated source revisions, the same toolchain/options, and an idle NPU. Build baseline and candidate separately; never replace a shared installation. The project contribution includes the portable benchmark and 52-case JSONL and native boundary/graph tests.

```bash
pytest -q tests/e2e/nightly/single_node/ops/singlecard_ops/test_sparse_flash_attention_kv_padding.py
python benchmarks/ops/benchmark_sparse_flash_attention_kv_padding.py --label baseline-commit --output baseline-b1.json
python benchmarks/ops/benchmark_sparse_flash_attention_kv_padding.py --label candidate-commit --output candidate-c1.json --reference baseline-b1.pt
```

The last two commands must run in the respective installations. Repeat B/C/C/B/B/C with fresh output paths/processes. Keep all `.json` samples and `.pt` output tensors. The public benchmark uses 8 native calls per graph, 10 warmup replays, 100 replays per timed sample (800 calls), and 25 eager calls plus synchronization per wall sample. Wall timing is amortized dispatch-inclusive time, not single-call latency.

The stricter generic per-element MERE/MARE criterion fails many baseline attention cases because reference values near zero amplify relative error; it is **not claimed to pass**. Arithmetic-preserving candidates instead retain project attention tolerances against an independent FP64 reference and byte-for-byte parity with baseline, including known baseline failures and empty-row statistics. This contribution does not include the separate empty-row correctness PR #17823.

Single-receiver DCP component evidence invokes the actual upstream index remap and device dispatcher with real NPU tensors and synthetic valid metadata. It does not construct a distributed group or execute query gather/output merge/model inference; these remain unverified.

Measured raw files are preserved verbatim. Some diagnostic JSON can contain Python's NaN/Infinity representation from baseline failures. Binary profiler traces, output tensors, build source archives and private package copies remain in the isolated cloud workspace, with source/artifact hashes in this evidence. Only numeric/log evidence, independent scripts and publicly licensed patches are published.

Original measurement scripts are provided under Apache-2.0. Upstream AscendC patch excerpts retain the CANN Open Software License 2.0 headers from their source files. No license is asserted for contest sources, which are not distributed here.

Final code commit: 5e51218dc3285dab1d58684d4804eb680fa51510. Candidate2 native pytest:56 passed; expanded88 pass FP64 reference and8 known failures retained; DCP receiver80 pass per build; public benchmark52 complete per build with output-byte/input-hash parity; both52-case profiles complete. See a2/correctness-report.md and raw logs.

## Findings and iteration decision

1. The upstream Cube schedule already shares selected KV across query heads and retains query data in L1. The contest's small FP16 vector/resident-KV shape assumptions do not directly fit the production D512/R64 operator; this patch changes neither scheduling nor arithmetic.
2. The removable cost is scalar per-row RoPE padding DMA. Reusing the existing zero key row reduces those commands by up to eight without extra clearing/allocation. The rejected A1 widened clearing and showed 32 higher medians; the final A2 confines the change to RoPE copies and shows useful nonempty, low-index-count device gains.
3. Gains are conditional. The complete A2 matrix still has 20 higher medians and a 3.39% worst device slowdown. Eager-wall benefit is inconsistent. A3/combined-prefix-trimming and model/distributed validation are outstanding, so this is a draft contribution with no model-speedup claim.

Final benchmark style pass names its seed/dimensions and sampling counts; values and the 800-call timing denominator are unchanged. Both original public-script measurements and a fresh run of the exact final script are retained in separate directories rather than pooled.

Exact final public benchmark script: both52-case runs complete; output-byte and all input-hash parity checks pass. Final style check format-ci-final-v3.log passes. Both earlier public runs and final public-v2 runs remain separate from the balanced acceptance samples.
