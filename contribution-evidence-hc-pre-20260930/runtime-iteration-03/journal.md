# Optional HcPre V2 output candidate

Hypothesis: the production V2 API returns only three tensors but allocates and
writes the optional fourth `pre` tensor. Omitting that unused output can reduce
allocation/dispatch and kernel writeback overhead without changing arithmetic.
Real callers: GLM5Next model.py:499 and DeepSeek V4 model.py:746.
V3 must retain all four outputs, including external pre_mix support.

Independent source worktree:
`/Users/jiaoziang/vllm-ascend-hc-pre-v2-20260930`, branch
`codex/hc-pre-v2-optional-output-20260930`.
Runtime commit 2ca077784546fbc5455ec42cd9c82ceed2b4a6a0; test/format correction
5fdc629a14a398539e531b6813abf5753f950fb6. Both DCO signed and pushed to the fork.
Baseline eee0ef7dfbe99a7ada56dafb3739dd952a0265b5.
Latest fetched upstream is 143861fd6931e388aa3609b8efd620dd8e3fd252. Target HcPre,
bindings, AGENTS and model caller files are unchanged; worker/SFA code changed.
Final upstream synchronization and model validation are still required.

No reduction candidate code or competition source is included. Binding uses an
undefined tensor for V2's optional output; existing ConvertType returns null,
HcPre definition marks pre OPTIONAL and tiling hasPreOut controls the copy.
Both original allocation and all returned outputs remain available in V3.

## Complete native builds and tests

Two private complete root-CMake native builds succeeded with identical flags:
baseline extension SHA256
43effca64fd404388ec990769102850306dbe56176c544516471c4f52ec1c6c3;
candidate extension SHA256
373dcdbaa0da348464ab90bf79a718d03d13c49186d67a4d541b979d370d0619.
Both direct-kernel libraries have SHA256
14723a803a4c9df04282074347d9b6d701e14484f1e9bc673c473707bc152622.
Both use the identical baseline HcPre OPP package, physical NPU 3 Ascend910B3.

Initial controller-v1 terminal exit 1: baseline 5 passed / 36 TypeError failures
because the new test called a missing CPU-oracle iteration parameter. No runtime
candidate correctness was established by that run. All initial logs remain.
Corrected test parameter preserves default 20 iterations, FP32 reference order
and error thresholds. Full format.sh ci passed with all new files tracked.

Controller-v2 PID 1254776: baseline/candidate normal nightly both 41/41 passed,
including CPU accuracy, shared-output byte parity, finite iterations 1/3/20,
signed inputs, 3D/4D input shapes and V2 graph replay. Tests run through normal
repository conftests and actual complete plugin, no collection bypass or stubs.
Baseline temporarily receives only the identical test file, then restores its
original file; per-run source/test hashes and backup are retained.

Extra tails: both variants pass 45/60 CPU cases, with identical input hashes and
CPU failure bitmap. Both pass same-process V2/V3, repeat, graph and input parity
on all 60. Candidate has six cross-process parity failures at t1/d7169 (all
requested iteration counts and both signs), affecting unchanged V3 as well as
V2. This is retained alongside the already observed identical-baseline tail
instability; neither baseline failure nor parity alone establishes accuracy.

## Pending measurements and integration

Controller-v2 runs complete V2-versus-V2 queued-graph A/A and ABBA (four processes
each), followed by eager ABBA. Every case/warmup/sample is retained. Graph
samples enqueue 32 replays of 20 complete calls per graph. Actual throughput or
stable per-case improvements have not yet been established.

Controller-v3 PID 1256620 waits for controller-v2 terminal success and its end
marker. It then runs actual decoder methods, production eager/graph L1 profiles,
isolated kernel file-open verification, an unpatched standard-loader model run,
and matched eager/graph models with the identical independent #17828 convolution
prerequisite. No live source is changed during controller-v2. The prerequisite
affects only this task's private model checkouts; shared environments stay intact.

PR #17821 still has head 52c8d05 and remains a draft test-only PR. Its body now
rejects the former first-add reduction based on all queued results and links
immutable evidence 2d54041acaedc41ed224d416e9e7bb34983ecfec. No optional-output
runtime change has been added to that PR and no performance claim is accepted.
Goal remains active and incomplete.

## Completed control and integration audit

All controllers v2, v3, v4 and v5 reached terminal exit 0 and their respective
completion markers. Their actual PIDs have exited. No tool timeout was treated
as a reason to restart a process. Local source was merged with upstream
568f6f555285f347006724f37ff4d03f6afb7283 at DCO commit
2c569adbd5b2dd85e775a11e4a283109d691fbca; full format.sh ci passed.
Cloud source remains the earlier explicitly recorded refs, so latest-worker
integration has not been established and must not be claimed.

Complete V2 benchmark comparisons, all 28 cases per experiment:

| Experiment | Geometric mean baseline/candidate | Faster / slower | Maximum slowdown |
| --- | --- | --- | --- |
| Graph A/A (same baseline code) | 1.008365 | 17 / 11 | 0.949% |
| Graph ABBA | 1.026566 | 27 / 1 | 0.163% |
| Graph BAAB | 1.005557 | 19 / 9 | 1.885% |
| Eager event A/A (same baseline code) | 1.106062 | 24 / 4 | 1.858% |
| Eager event ABBA | 0.998681 | 14 / 14 | 2.638% |

Independent-process pair geometric means are retained in the corresponding
JSON summaries. Graph ABBA pairs differ markedly (1.051729 / 1.002282);
eager ABBA pairs reverse direction (1.034402 / 0.966901). Eager same-code
control pairs are 1.004283 / 1.151980: an apparent 10.6% pooled gain exists
without a source change. All warmups, measured samples and slowdown cases
remain available. These controls prohibit attributing the pooled apparent
gains to this candidate. No unique physical cause of the drift is proven.

L1 profiling establishes a concrete reduction in allocation requests: every
eager case has 60 HcPre calls, baseline 300 aten::empty events and candidate
240 (5 versus 4 per call, including workspace). The nested empty_tensor
events are not an additional allocation count. Output Shapes confirms the
optional fourth output is omitted. Graph replay has no allocations in either
arm; allocations happen at capture. Logical omitted FP32 output bytes are
16 * tokens for hc_mult=4; actual allocator peak/pool reduction is unmeasured.
Both arms actually open the identical e4fe3ba HcPre kernel object.

All seven eager profiled kernel medians improve, but all seven graph profiled
kernel medians regress. These are diagnostic timings, not benchmark samples;
all 28 profiles are retained and reproducible with analyze_profiles.py.
Reduced MTE3 work does not establish a shorter critical path or stable latency.

Actual GLM decoder methods pass 24/24 cases in both variants. Matched standard
DummyModelLoader four-layer BF16 GLM smoke passes in eager and graph: each
mode compares 4 requests, 32 generated tokens and 160 finite logprob values,
with exactly identical outputs and model config SHA256 f259aa655d23962ee587ca2c0449867204ae7ad4b1e218fc36865a66765f481e.
Both use the identical independent #17828 causal-convolution prerequisite;
the unpatched baseline multi-request failure is retained separately.
This proves functional smoke parity, not trained-checkpoint accuracy or
model throughput. The new full-model graph profiler completed both arms;
its replay/kernel traces still need independent parsing before replay counts
can be cited.

Conclusion: reject this candidate as an established latency optimization at
this stage. The unused allocation/writeback reduction is real, but stable
inference latency gains are unproven. Keep it separate from PR #17821, which
was rechecked at draft/test-only head 52c8d05. Continue investigating measured
critical paths; do not count tests, allocation counts or model smoke as goal
completion. Optional-output evidence publication and final latest-source
cloud validation remain pending.

Full-model profiler evidence was subsequently snapshotted without changing
either source or environment: actual-model-profiles-v1.tar, 31,897,600 bytes,
80 text files, SHA256 56d50292485bd04b451796431dabbaddfb131d8d01fd0dfb40d3897b72ff984c.
Downloaded gzip SHA256 49bea05d40a5e6ed100de533f38be5241601474cab422be333566f8b3191699a.
analyze_model_profiles.py independently verifies both arms: 14
aclmdlRIExecuteAsync events, 136 HcPre tasks, of which 112 have graph model
IDs 47/48/49 and 24 have eager ID 4294967295. Both actual full-model runs
contain 8 requests, 64 generated tokens and 320 finite logprob values with
exact parity. This is functional/replay proof and does not establish model
throughput or rescue the rejected operator performance claim.
