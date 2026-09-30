# Contiguous HcPre Cast candidate

Previous turn classification: progress. All optional-output comparisons were
analyzed, including reverse order and same-code controls, and the candidate
was rejected as a proven latency optimization. No goal completion is claimed.

## Hypothesis and source

Competition source at 4546d1864b3a16da3fc8bfe5ad3b06de380526bd uses contiguous
count Cast where the layout permits it. Independently apply that generic
mechanism to the existing upstream CastTwoDim helper: when both source and
destination row strides equal the logical row width, issue one count Cast
instead of one per row. Keep dtype, rounding, barriers, padding fallback,
reductions, finite Sinkhorn iteration order and public interfaces unchanged.
No competition code was copied; its missing repository license does not
authorize importing it. Preserve the existing CANN OSLA-2.0 source header.

Actual affected callers are HcPre Stage 1 input conversion and Stage 2
ProcessY's four residual streams. GLM5Next and DeepSeek V4 call this operator.
Aligned rows use the new path; nonaligned/tail rows retain their original
source and destination strides. Benefits are unverified. Source-level Cast
call reduction alone does not prove emitted-instruction or latency reduction.

An earlier proposed batched column-Div path was not implemented: inspection
of UB tiling showed large production hidden sizes often have stage2RowFactor
1, undermining its expected benefit. Do not invent a benchmark-only call site.

Independent worktree: /Users/jiaoziang/vllm-ascend-hc-pre-cast-20260930.
Branch codex/hc-pre-contiguous-cast-20260930, DCO-signed commit
5983ac07f62095c1e7fa725e0b7f9ce692e8d5f1. Baseline latest upstream
11682d1e341d161a4129a58863f39a912846f71d. Target kernel and binding were
unchanged from prior upstream baseline, but root CMake and other runtime
files changed. Build both complete native extensions and OPP packages fresh.
New open-HcPre PR search did not find a duplicate runtime Cast contribution;
pending PR #17122 concerns A5/V4.1 and a different kernel branch.

## Checks and current state

Full format.sh ci passed before and after the DCO commit. Normal nightly
validation uses the original five tests plus 36 finite-iteration, V2/V3
parity, input-preservation and graph tests. Tests keep the existing FP32
CPU oracle and thresholds. The baseline temporarily receives the identical
test update, then restores its source file.

At the pre-upload cloud check NPU 3 was Ascend910B3, health OK, 38 C,
with no running NPU processes and the foreign-job guard clear. Prior
controller-v5 reached exit 0 and its terminal completion marker.

Upload was interrupted when the existing port-forward connection closed.
Subsequent SSH was refused. Inspection after connection recovery found no
controller PID/log and only a 128 KiB partial bundle. No build start was
established. Re-upload uses a separate .partial file, and requires exact
SHA256 3db824fb6673b48ad18d9ce6c178eb9745bc11f75267ebbb39b908de80ffe112
before replacing this task's interrupted transfer and starting the controller.
No shared source, environment, dependency, process or tunnel was changed.

Controller-v1 builds matched fresh OPP and native binaries, runs normal
nightly, records all 60 boundary cases including failures, actual decoder
methods, and complete production V2 graph ABBA. Boundary exit 1 is retained
as failure data, never interpreted as correctness passing; its presence
does not prevent collecting diagnostic performance results. All cases and
raw samples remain. A terminal controller completion marker denotes
orchestration completion, not proof that every diagnostic case passed.

NPU results and performance are pending. No source was added to PR #17821.

The repeated full-bundle transfer also failed, leaving 192 KiB in its
separate .partial file. To avoid redundant history transfer, a Git-verified
incremental bundle was prepared (251 KiB), requiring existing base eee0ef7.
The private optional-pre-source-baseline repository was checked to contain
that commit; full-plugin-source-v3 did not, so the fresh-clone source was
corrected before launching any build. Cloning copies committed objects only,
not that private checkout's working convolution prerequisite patch.
Legacy SCP transferred the incremental bundle successfully. Its remote
SHA256 exactly matches b87b37cb3ee5d570b6f1d615ba44e0d54bd632f4b5605c72f8559fed7d0ff7b9.
Both interrupted full transfers are retained. The controller is only started
after this verified upload; its PID and actual process must now be checked.

Controller PID 1341446 was subsequently verified live. Its actual child
Python build_matched.py PID 1341580 was also verified live, with a growing
build.log, no terminal exit file, foreign-job guard empty, and the NPU
pre-build inventory recorded. This establishes a real active build, not
merely an intended launch or a stale lock. Do not restart after polling
timeouts. Fork ref codex/hc-pre-contiguous-cast-20260930 was independently
checked to point to 5983ac07f62095c1e7fa725e0b7f9ce692e8d5f1.

## Follow-up execution and audit

While the fresh matched builds remained in their build-only stage, unexecuted
caller/profile/file-open drivers were updated to refer to iteration-04's
identical input/oracle files. Both sources and the active builder stayed
unchanged. The model driver now explicitly invokes the accepted standard
DummyModelLoader profiling script from iteration-02, which preserves actual
repository model methods and records graph execution. All updated drivers
were uploaded before any validation phase started.

Controller-v2 PID 1345654 and controller-v3 PID 1345655 were verified live,
waiting on predecessor exit files/completion markers. They serialize graph
A/A, reverse BAAB, eager ABBA, eager A/A, actual kernel file-open proof,
operator L1 profiles, identical private #17828 prerequisite, and full actual
eager/graph models. They do not launch overlapping device work. Completion
and acceptance must be assessed from individual raw results, not a waiting
controller or an orchestration marker.

Top-level baseline OPP build.log appeared unchanged for several minutes at
the protobuf build command. observe_controller.py inspected actual descendants
instead of restarting: libprotoc's g++-13/cc1plus processes were active
(observed CPU 105% and 194%), with new leaf PIDs under the same build parent.
The build is making progress while its wrapper buffers output. No genuine
blocker or source/compiler error has been established. No restart, shared
environment update, competing compiler job or NPU workload was introduced.

PR #17821 was independently rechecked: still draft/test-only head 52c8d05.
This Cast candidate is only on the independent fork branch. Stable operator
performance, latest-source normal nightly/model results and public final
evidence are pending; the full goal remains active.

CANN 9.1.0's actual dav_c220 Cast count implementation was inspected at
compiler/tikcpp/tikcfw/impl/dav_c220/kernel_operator_vec_vconv_impl.h:801.
It takes uint32_t count, enters mask-count mode, sets the count, executes
CastIntrinsicsImpl using contiguous source/destination repeat strides, then
restores normal mask mode and the full mask. BF16-to-FP32 uses source repeat
stride 4/destination 8; reverse uses source 8/destination 4. Combining
contiguous rows therefore removes repeated API-level mode/count management
while preserving scalar element conversions. This is verified SDK source
mechanism, not proof of emitted-instruction counts or speedup. Nonaligned
row layout retains the original Cast calls. No approximate reciprocal,
floating-point reduction reordering or shortened iteration count is used.

The actual-model optional-output trace archive and this round's inputs were
scanned by gitleaks with no leaks found. Driver/build hashes were frozen in
driver-input-sha256.json. Baseline OPP packaging and full root-CMake native
build subsequently completed; controller-v1 advanced to candidate OPP build
without a restart. Numerical/model/performance validation still awaits both
complete candidate artifacts. Hardware timings remain unproven.

Baseline native/OPP manifest is downloaded as baseline-binary-sha256.json:
extension 87f2598dee7a34ad78d3e1af6e9c5f4c0f44e5807cd19098f8e8f2a6f77d39ac,
direct kernels eebb909c05e51a0c6707097405abde63643448c33a718c0aa55ff533eaf01f50,
HcPre object e4fe3ba278578281a0bb142d5da21cbfeb6d55e355378112fc429440eea23622.
Candidate CANN HcPre object and relocatable compilation both reached their
Generating ... Done markers at 19:57:06 and 19:57:29. Full candidate packaging,
native build and NPU validations are still pending. At the final observation
controller 1341446 and builder 1341580 were live, as were gated waiting
controllers 1345654 and 1345655; no terminal controller-v1 exit file existed.

## Reviewable benchmark and documentation

DCO commit 27305b8c19aff8dfeda959da1cc264362cb34be8 adds the installed-plugin
complete HcPre benchmark and documentation to the candidate branch. Full
format.sh ci passed for all five changed files, and the commit was pushed to
the independent fork branch. The tracked benchmark and frozen cloud driver
have identical SHA256 011144fd9193fe946979eda950ec5e8a94ee9ee03a60aa4839cef68351239076.
Documentation explicitly marks candidate correctness/performance pending,
preserves all cases, warmups and wall/event samples, requires intended kernel
load proof, and excludes model throughput claims. Runtime and test sources
remain identical to the 5983ac0 build ref.

Fresh upstream fetch found 5fa57c55bb37861d3da0274fbf7a28d15d745b87 (hybrid
non-contiguous KV cache #14340). HcPre, its bindings, CMake and AGENTS are
unchanged, but GLM pooled-cache, model runner, attention and mamba paths have
changes. Existing live cloud cohort remains pinned to 11682d1/5983ac0;
do not mutate these sources mid-run. Final latest-source model integration
will need revalidation. Installed vLLM metadata was independently read as
0.1.dev1+gced6857af.empty; upstream source remains ced6857afa0ea7b2e3f0846a62e1394e90f15607.

Local candidate was synchronized with upstream 5fa57c5 using DCO-signed merge
8b93b17c9f346e566674033322f34028b6a0c7ed. Full format.sh ci passed after
the merge and the fork was pushed. The runtime helper, binding, CMake and
normal-nightly test file have no diff relative to the frozen cloud candidate
5983ac0. Cloud worker/model cohort remains at its original recorded ref;
the local merge is not evidence that cloud model validation used latest KV
cache changes.

## Complete matched builds and first NPU results

Both full builds reached MATCHED_NATIVE_AND_OPP_BUILD_PASS. Candidate native
extension SHA256 a1e2ea54428fad862a121f3f2fe9554e88b71e6024e0d8514604fdfd1734687f;
both direct-kernel libraries eebb909c05e51a0c6707097405abde63643448c33a718c0aa55ff533eaf01f50.
Candidate HcPre object 8ea96b95a26ed2048d1ba532845e29413b69491bc8bbf216040e529a8fa42fd2,
relocatable object 1fa19198c2e8711389defe5b925682bdbdd375998aed1fdc224e0266ab50a12f.
Different extension hashes do not imply a binding source change: both use the
same binding and compiler settings in different build/source paths. Full
compile_commands, CMakeCache, source refs and manifests are retained; actual
OPP kernel selection still needs the queued separate file-open diagnostic.

Normal repository nightly collection passes 41/41 in both exact full-plugin
arms: baseline 7.85 s and candidate 7.74 s (test-suite elapsed times are not
benchmarks). Original five tests plus 36 added finite-iteration, signed-input,
V2/V3, 3D/4D, input-preservation and graph cases use unchanged CPU thresholds.
Each has 14 retained warnings. This establishes this suite's correctness at
the frozen refs; it does not count pending boundary or model checks as passed.
The controller advanced to 60-case boundary diagnostics. Performance, actual
model integration, latest worker revalidation and acceptance are still pending.

## Terminal validation and rejection

All three serial controllers terminated with exit 0 and their completion markers.
The text snapshot contains 1,199 files, gzip size 8,605,693 bytes, SHA256
6e6b089c673eccdfd0072c93446eb8dc48e2cc7517d1327eed7bac918cdd348b.
The archive retains boundary exits 1 instead of converting them to passes.

All comparisons pool every measured sample (150 per arm/case) and expose
all six round medians and both independent process medians.

graph-abba: geometric mean speedup 0.978565531; independent pairs [0.9831686147450488, 0.9727304794530892]; 4 faster / 24 slower; maximum slowdown 7.538737%.

graph-baab: geometric mean speedup 0.994634162; independent pairs [0.9658300833746614, 1.025007543227202]; 9 faster / 19 slower; maximum slowdown 4.209548%.

graph-aa: geometric mean speedup 0.982400785; independent pairs [0.998314365421363, 0.9689469859946244]; 5 faster / 23 slower; maximum slowdown 5.195160%.

event-abba: geometric mean speedup 1.056090783; independent pairs [0.9856137376686954, 1.0793840452883932]; 15 faster / 13 slower; maximum slowdown 4.572575%.

event-aa: geometric mean speedup 1.015264779; independent pairs [1.00639169747652, 1.0069553104947524]; 13 faster / 15 slower; maximum slowdown 2.583321%.

**Reject as a demonstrated inference latency optimization.** Both graph
comparison orders regress overall; eager pairs disagree in direction. A/A
shows variation and does not authorize subtracting its pooled drift from
candidate measurements. No stable critical-path gain is established.

Separate LD_PRELOAD diagnostics observe the actual intended HcPre objects:
baseline e4fe3ba278578281a0bb142d5da21cbfeb6d55e355378112fc429440eea23622;
candidate 8ea96b95a26ed2048d1ba532845e29413b69491bc8bbf216040e529a8fa42fd2.
Timing has no LD_PRELOAD instrumentation. L1 profiles retain 28 cases, each
with 60 HcPre kernel observations. Vector counter time is slightly lower in
all inspected cases, but scalar and kernel durations vary or regress, and
complete-operator graph results do not improve. Fewer source Cast calls
therefore do not establish a shorter critical path.

Actual decoder validation passes 24/24 per arm and all serialized output
hashes match across arms. Standard DummyModelLoader GLM eager and graph
functional JSON is exactly equal between variants: eight requests, 64 tokens,
320 finite logprob values each, maximum difference zero. Both use the same
private independent convolution prerequisite from #17828. Actual model graph
traces show 14 aclmdlRIExecuteAsync events and 136 HcPre kernels per arm:
24 eager and 112 with captured model IDs 47/48/49. This is synthetic
functional integration, not trained-checkpoint accuracy or model throughput.

Boundary results remain 45/60 CPU passes each, identical failing-case bitmap
and input hashes; candidate additionally fails six cross-process parity cases
at t1/d7169. No boundary failure is presented as a candidate pass.
The successful builds/models are pinned to 11682d1/5983ac0; the local latest
5fa57c5 merge was not cloud revalidated. Since the candidate is rejected,
latest-source final acceptance validation is deferred to the next viable
runtime candidate. PR #17821 remains test-only, and the goal remains active.
