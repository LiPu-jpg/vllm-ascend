# SFA nonempty performance investigation

Baseline: upstream `eee0ef7dfbe99a7ada56dafb3739dd952a0265b5`, fetched 2026-09-30.
Worktree: `/Users/jiaoziang/vllm-ascend-sfa-perf-20260930`.
Branch: `codex/sfa-nonempty-performance-20260930`.
No SFA changes between previous audited baseline e86df70 and this revision.
PR #17823 and mHC work remain independent.

## Provenance

R152 source is recovered at `../vllm-ascend-sfa-evidence-20260930/r152/source`.
Its archive has no explicit license declaration. Algorithmic ideas are studied;
implementation is independently written in the public upstream code. No contest
implementation is copied. Historical R124 score 73.3 exceeded final R152 69.87;
the historical audit says R152 retained 34 fast functions and expanded fallback
coverage. Historical scores are not measurements on production vLLM inputs.

## Mechanism comparison

| Contest mechanism and source | Conditions | Existing upstream mechanism | Additional opportunity / status |
|---|---|---|---|
| Resident packet KV; kernel lines 68-73, host lines 79-136 | FP16, D32/64, R16/32, <=4 selected keys, <=8 heads, <=32 KiB KV | V-template gathers selected KV once per tile, Cube processes all heads; Q is held in L1 within a tile | Full-cache residency does not generalize to long paged caches. A D512 small-selection vector path is a hypothesis, not a demonstrated improvement |
| Grouped head reuse; kernel GroupScores / ProcessGroupedToken lines 967-1045 | Aligned D, groups of 2/4/8 heads | Host SplitBalanced mBase=gSize; Cube N/K loops enclose M loops and reuse each KV tile | No evidence yet of redundant per-head gathers in the ordinary <=128-head upstream path. Do not reimplement existing reuse |
| Query packets P=2/4; host lines 101-108 | Whole packets, no batch crossing, one wave | Separate top-k set per query; mBase contains one query's heads | Cross-query batching requires different sparse sets and paged metadata. Prototype only if profiling justifies extra complexity |
| Bulk DMA overlapping scalar index processing; kernel lines 68-115 | Small resident packet | Two-row strided gather, 32-row UB ping/pong, 4 GM staging buffers, 3-stage Cube/vector pipeline | Confirmed scalar per-row zero-fill loop remains at vector service lines 1045-1068. First candidate batches those writes using existing 32-row UB storage |
| Block/whole reductions and buffer reuse; kernel lines 157-193 | Fixed D32/64 layouts | Existing softmax service / FP32 accumulation / NoPE specialized Cube path | Replacement needs a numerical and workload-specific performance proof; not automatically superior |

All upstream paths above are in
`csrc/attention/sparse_flash_attention/op_kernel/arch22/`; host tiling is in
`op_host/sparse_flash_attention_tiling.cpp`. Missing design.md / testcase-gen
documents: cases are independently designed from README, host checks and actual
call sites, not from generated contest cases.

## Actual consumers

`AscendSFAImpl` calls the native operator for RoPE MLA. Floating NoPE outside
DCP dispatches to sparse_mla: its branch without smla_metadata calls this native
operator too (sfa_v1.py lines 230-249), whereas the A5 metadata branch uses
sparse_flash_mla. `AscendSFADCPImpl` remaps replicated
top-k indices to a compact local prefix and pads the rest with -1; decode calls
TND / PA_BSND, mode 0, return_lse=True. Prefill uses mode 3 and return_lse=False.
These consumers establish real nonempty partially filled rows. Runtime shape
frequency still requires measurement; no full-model improvement is claimed.

## Overlap audit

- #17653 (ShuZihan), OPEN, head 228695eb49afd8d7f189fea710bd7bac70558257,
  isDraft=false at this inspection although its description still says draft:
  A3-only valid-prefix detection shortens computation. First candidate does not
  detect prefix length or shorten any computation; it optimizes existing writes
  in the shared A2/A3 arch22 path. Benefits may overlap on A3 when #17653 lands.
- #15173 sorts logical sparse indices in Python for determinism; different scope.
- #16656 merged A5 empty-shard statistics, #16252 merged NoPE backend,
  #17594 merged cache-store dispatch: no duplication.
- GitHub search `SFA padding` yielded no additional matches; this is not proof
  that no external work exists.

## First experiment

Candidate A: bulk zero filling of staged KV tails. Use up to the existing 32-row
buffer capacity, initialize only min(remaining,32) rows, then one contiguous
DataCopyPad per chunk (and per RoPE plane when present). Preserve existing
MTE3-to-vector wait, buffer-reuse events, valid counts, and all attention math.
All-valid rows never enter this branch. No new tiling key, allocation or config.
Potential benefit is reduced scalar/DMA issue overhead for NONEMPTY padded rows;
unverified until paired native-NPU measurements.

Candidate B: D512 selected-KV vector path. Retained as an alternative requiring
an independent implementation and measurements if A is insufficient.

## Device scheduling

2026-09-30 inspection: visible device physical 3 / Ascend910B3, 64 GiB HBM,
driver 25.5.0, healthy. Another work's queued_graph_control.py (PID 1225626)
occupied the device at 40% AICore. No NPU tests or builds started by this task.
Use a private remote directory and recheck live processes before execution.

## Initial native result and expanded correctness

Candidate A builds on Ascend910B3 with CANN 9.1.0, Release/O3,
`bash build.sh --opkernel --soc=ascend910b --ops=sparse_flash_attention -j2`.
Generated source SHA and both installed SFA object hashes are recorded;
framework/host adapter libraries match the baseline. No shared runtime is edited.

60 initial numerical configurations pass the project's nonempty output/LSE
tolerances and are byte-identical to baseline for all three outputs. The baseline
strict-empty-zero assertion initially stopped on BF16: the existing AMLA 2^-80
initial bias survives BF16 conversion. Original failing logs and test-driver
versions are retained, and subsequent runs explicitly report these tiny values.
The generic elementwise MERE/MARE criterion passes only 2/28 nonempty cases per
dtype on the ORIGINAL baseline; near-zero attention components amplify relative
error. This patch does not improve that criterion: all errors match bytewise.
It must not be described as passing that generic precision criterion.

96 additional layout/mode/block configurations complete on both builds, with
every output byte identical. They cover TND, PA_BSND, BSND; mode 0/3; block 1/2/4
(changed V-template) and block 8 (unchanged C-template); heads 1/8/64/128;
FP16/BF16; RoPE64/NoPE. Eight BSND/block8/head1 cases fail their LSE reference
on BOTH builds (one nonempty row has NaN); outputs and raw stats remain identical.
All eight failures are retained and are not reclassified as passes.
An initial direct import of device_op caused a circular import in the isolated
package. Loading the normal ops registry first resolves it. Real
BaseDeviceAdaptor.execute_sparse_flash_attention_process with synthetic paged
KV/metadata now passes the reference and exact native comparison for mode 0 and
3 on both builds. This is dispatcher validation, not full model inference.

The initial 16-case quick comparison gives mixed results: RoPE selected=1
improves 4.7–9.1% in speedup ratio, whereas other configurations are unchanged
or slower (up to 3.24% in this single-process comparison). It is preliminary;
the fixed 52-case balanced six-process study is the acceptance evidence.
It adds query batches, 511-row tails, 4096-token KV caches, multiple KV tiles
and fully valid 2048-entry rows. All cases are nonempty.

One candidate layout run and one candidate paired run detect another work's
NPU process and exit 75. Their partial logs/samples are retained, and are
excluded from the final balanced comparison. The controller waits for that
work's live process AND queued controller to finish. It is never terminated
or modified by this task.

#17653's SFA host/kernel changes apply cleanly in a filtered git apply --check.
The complete older patch does not apply cleanly because its quantized README
has drifted on current main. No combined A3 compilation or performance claim
is made. Source-level compatibility is weaker evidence than hardware testing.

Latest upstream reinspected: 568f6f555285f347006724f37ff4d03f6afb7283.
SFA sources, device dispatcher, DCP caller and AGENTS.md have no changes since
the locked eee0ef7 benchmark snapshot. The independent contribution branch is
rebased to that newer integration base; native artifact comparisons still refer
to the explicitly recorded identical SFA source snapshot. Local Signed-off-by
commit a80ee36fc51065fa46ed4b598bea125f5441c434 preserves the experimental
candidate; no performance PR is created before acceptance measurements finish.

## Second candidate: reuse the existing zero key row for RoPE

Independent candidate commit: 640eb70 (parent a80ee36 preserves candidate A1).
Source SHA256: 489daf734b639dbd6afb25ed661f250ff4d161e076d55171f4267ce61b749191.
The private `iteration-a2` directory denotes iteration 2, not the A2 device family.

Candidate A1 clears up to 32 KiB rather than the baseline's 1 KiB. The first
complete paired process still gives mixed results, especially for NoPE. Extra
clearing is a plausible cost, not a proved cause of those regressions; clock
variation and compiled instruction placement also remain possible.

Host checks at tiling.cpp:1369–1384 constrain D=512 and RoPE=0/64. The existing
zero key row contains 512 FP16/BF16 elements and can therefore supply eight
contiguous 64-element RoPE rows without another vector write. Iteration 2
retains the ORIGINAL Duplicate, key-copy loop and synchronization, and changes
only the RoPE-copy loop. The final short copy uses min(remaining,8), so neither
AIV partition can write past its limit or read more than the zeroed key row.
The actual implementation derives the row ratio from the validated dimensions.
NoPE and all-valid rows skip the added loop by their existing guards. This is
a source fact; their measured performance still must be reported fairly.

The complete csrc archive, patch and source hash are preserved independently.
A private installer verifies generated/installed artifacts and framework/host
library parity. A separate controller waits for candidate A1's complete
measurement/pytest stage before building iteration 2. It then runs the same
60 numerical cases, 96 layout cases, both real-dispatch checks, and a fresh
52-case B/C/C/B/B/C comparison. Native compilation and 60 numerical cases now pass; all 96 expanded-layout outputs and both real-dispatch checks match the locked baseline bytes (the same eight existing BSND/block8/head1 LSE reference failures remain). The 52-case B/C/C/B/B/C comparison is complete; profiler and the final pytest stage are still pending.

Both iterations' queued profiler uses the installed torch_npu 2.10 API's Level1
and PipeUtilization counters with warmup=5/active=5. The previous profiler driver
is saved as profiler_v1.py; no profile had begun before this update. Profiler,
case and test-driver hashes are written to the report. Profiled durations remain
diagnostic and are never pooled with unprofiled benchmark samples.

## Complete unprofiled comparisons (2026-09-30)

Both use exactly the same 52 fixed nonempty cases, each with 15 raw graph-device and amortized eager-wall samples per variant from three independent processes. Fresh baseline processes are used for each candidate. Input hashes match. Native profiler is separate.

| Iteration | Lower / higher device medians | Largest lower latency | Largest higher latency | Decision |
| --- | --- | --- | --- | --- |
| A1: batch KEY+RoPE, clear up to 32 KiB | 20 / 32 | 6.91% | 3.39% | Preserve all results; do not submit as final |
| A2: RoPE only, reuse existing 1 KiB zero row | 32 / 20 | 7.33% | 3.39% | Promising scoped improvement; finish native profiler, pytest and receiver-component check |

Neither iteration demonstrates consistent amortized eager-wall improvement or whole-model speedup. A2 case 23 (BF16, RoPE64, Q32, KV512, 512 selected) regresses 3.39%; NoPE case 40 (BF16, Q1, KV4096, 127 selected) regresses 2.91% despite unchanged source logic. These observations remain in the acceptance table; we do not dismiss them as noise. A2's four single-query/one-selected/RoPE64 cases improve 5.69–7.33% in pooled medians, with all three candidate process medians lower than all three baseline process medians for cases 6,18,46; ranges overlap for case32. No statistical significance is claimed.

Candidate A1 native pytest baseline/candidate: 56 passed each. Public benchmark input construction: all 52 SHA256 values match measured workloads. Candidate A2 final pytest and execution of the public benchmark are queued independently, after the profiler.

Upstream recheck: main 11682d1e341d161a4129a58863f39a912846f71d; no diff in SFA source, DCP caller, device dispatcher or AGENTS.md relative to integration base 568f6f5. PR #17653 remains OPEN, non-draft, head 228695eb49afd8d7f189fea710bd7bac70558257. #16252 is merged. The runtime DCP caller whole-file SHA256 matches the integration base. The dispatcher whole file differs (unrelated cache-store changes); its SFA method hash will be checked explicitly in the actual receiver component evidence.

## Final validation and contribution

Final code commit 5e51218dc3285dab1d58684d4804eb680fa51510, based on 11682d1, contains only the A2 RoPE-buffer-reuse candidate, benchmark/cases, new native tests and README. Source hash remains 489daf734b639dbd6afb25ed661f250ff4d161e076d55171f4267ce61b749191; rebase/squash did not change measured kernel source. Both experimental commits are retained on independent local refs and their patches/results remain in the evidence. DCO sign-off and final format.sh ci pass.

Candidate2 native pytest: 56 passed. Both 52-case native profiles are complete; candidate profiler attempt1 aborted before its first case when another task used the NPU, and fresh attempt2 completed. All interrupted attempts are retained. Actual single-receiver DCP remap/backend is Triton: 80 checks per build passed; actual SFA dispatch function text matches latest upstream exactly. AST hashes cannot be compared across Python3.9/3.12; canonical method text parity is recorded. Public benchmark runs both complete all52 cases, check baseline output bytes, and match acceptance input hashes; their additional timings are reported separately without pooling.

Decision: retain the smaller A2 implementation for a **draft** upstream contribution with qualified operator-only gains and all regressions visible. A3 device/compile, combined #17653 validation, distributed collectives, full-model performance and maintainer-triggered CI remain outstanding.

Exact final public benchmark script: both52-case runs complete; output-byte and all input-hash parity checks pass. Final style check format-ci-final-v3.log passes. Both earlier public runs and final public-v2 runs remain separate from the balanced acceptance samples.
