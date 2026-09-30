# Iteration 02: registration controls, stable timing and integration

Goal remains active and incomplete. Prior goal turn made progress: runtime
candidate d50abbec was implemented, built, signed off, and passed 53 normal
nightly cases, with raw diagnostics published. This turn revalidated the
specific waiting controllers and the independently progressing competing
profiling processes; none was restarted or terminated by this task.

Upstream is now 88aebfb2dad70efb5721c1691a91b12f30299b25 (#17115).
Diff inspection shows no changes to HcPre or the target model callsites.
Candidate worktree remains clean at d50abbec269b1f55983f122388d608b0fab38a62.

After the competing sequence terminated, validation-v4 proceeded. Normal nightly
candidate: 53 passed in 9.33s. Actual GLM decoder methods: baseline 24/24,
peeled candidate 24/24; eager/graph, CPU oracle and candidate/baseline bitwise
checks passed. The original decoder methods and registered native operators
ran without mocks. This is method integration, not whole-model generation.

A/A measurements of the same baseline kernel gave geometric mean 1.0206293,
with apparent improvements in 25/28 cases and per-pair means 1.01631/1.02726.
All serialized outputs have equal hashes. Several small cases drift by 3-4%.
This establishes a nonzero measurement noise/bias floor even with idle guards;
it does not identify a specific hardware/allocator cause. It prevents accepting
a small pooled ABBA gain without more controls. All six medians per arm and
300 measured samples per arm remain retained; no confidence interval assumes
independent samples within a process.

Historical original-candidate medians also drift across its two processes.
For t512/d7168-positive, standalone round medians move from ~172-173us to ~168us.
A standalone-vs-production attribution is not justified by those records alone.

Device power queries work, but this npu-smi build rejects both `-t npu` and
`-t common`; clock values are unavailable through the inspected interfaces.
Those errors remain retained, and no frequency/power setting is changed.

The v4 controller subsequently stopped with exit 1: another task began a new
NPU sequence. Its original-candidate baseline-b arm completed but its final
device snapshot contains foreign PID 1166612, so that complete ABBA is invalid
for fair performance claims. Its descriptive summary (1.00917 geometric mean,
17 faster / 11 slower, maximum slowdown 3.2719%) remains retained under an
explicit invalid-concurrent label. No arm is dropped to construct a gain.
The peeled baseline-a arm completed; peeled-a failed its idle guard before
Python execution. Models did not run. Followup and steady controllers both
terminated with exit 1, with steady-aa-a1 failing before data collection.
No crashed or guard-failed result directory is overwritten.

At 07:26 UTC the competing controller and NPU process had terminated. Device
and broad process checks were idle. A fresh idle-controls-v1 controller (PID
1214774) was launched with new result names and before/after interference
guards. All three diagnostic trace processes succeeded and observed the
actual variant-specific .o file opens; hashes match the frozen baseline,
original candidate and peeled binaries. LD_PRELOAD is used only for these
diagnostics, never timing. Long-warmup A/A and peeled ABBA follow sequentially.
Permission to message the other chat for scheduling is pending; no cross-chat
message was sent. Other tasks' processes and sources remain untouched.

Controls prepared for sequential execution:
- Actual kernel binary opens and hashes, including multi-vendor resolution.
- 120 small/aligned-repeat-tail/unaligned-tail/external-pre_mix cases with the
  unchanged upstream CPU oracle. Baseline accuracy failures stay failures;
  bitwise parity cannot relabel them as successful candidate accuracy.
- Historical probe and production registration using the exact same original
  benchmark.make_inputs/measure functions, schemas/options recorded, fresh
  processes, all 28 cases and ABBA order. Probe scope is isolated diagnostics.
- Eager L1 profiling for real ACL-to-NPU flows and original/peeled kernel counters.

A/A's remaining drift motivates a warmup control using 500 rather than 20 graph
samples (each sample is 20 HcPre calls). This hypothesis concerns runtime warm
state, not proof of DVFS. Keep all warmups and do not replace historical runs.
Compare A/A first under the expanded warmup, then repeat peeled ABBA if stable.
Whole-model stock-dummy smoke and the prepared controls are not yet claimed
successful. The native full extension remains reused from an equivalent HcPre
binding section; a fresh source-exact full extension build remains desirable.

Verified the official diff and head of dependency PR #17828, cbb707903e619db01439e19731b0e688377326fe.
It fixes packed convolution null-slot handling, independently of HcPre.
Any model run using it must record this patch and use it identically for both
arms in an isolated source directory. The unmodified-head result must remain
distinct; no model pass is implied by another PR's smoke.

## Long-warmup controls completed

idle-controls-v1 stopped before timing: the installed torch_npu 2.10 config
descriptor exposes allow_internal_format as write-only, and metadata attempted
to read it. The failure and logs remain retained. Fixed metadata records the
explicit requested value and labels the effective getter unavailable; no runtime
value was silently changed. idle-controls-v2 uses fresh names and completed all
four A/A and four peeled ABBA arms with before/after process guards.

At warmup=500, same-kernel A/A is still unstable: geometric mean 0.98566094,
5 apparent faster / 23 slower, maximum apparent slowdown 3.78195%. Thus extra
warmup alone does not remove the problem. The d50 candidate ABBA gives 1.01638088,
22 faster / 6 slower, maximum slowdown 4.30223%, with per-pair means 1.02156 and
1.01143. All outputs remain byte-identical. This is provisional, not accepted
performance. Full samples and all round/process medians are retained.

Hypothesis: the external timing-event window includes device idle time between
host event submission and graph replay submission. Inspection of the benchmark
confirms this window; it does not prove this is the cause of all historical
variation. queued_graph_control.py captures the same 20 complete HcPre calls,
then enqueues 32 graph replays per external event pair without intermediate host
synchronization. Per-op elapsed time divides by all 640 complete calls, and
synchronized wall time is also retained. This is a new steady queued-graph
measurement, distinct from the original single-replay results and from model
throughput. First validate it with A/A, then compare the candidate. No benchmark
function, registration or loader is monkeypatched. Original timings stay intact.

The integration controller built a full extension/direct kernels from exact
source d50abbec using official root CMake arguments. Build succeeded:
vllm_ascend_C SHA256 50de6a4f00129b30c7121aa14d8d86c80d7ee9a0ce32f8bf027143e158d4a5de;
direct kernels SHA256 14723a803a4c9df04282074347d9b6d701e14484f1e9bc673c473707bc152622.
Normal nightly against this fresh full extension: 53 passed in 9.32s.
Unpatched-head standard-dummy GLM eager smoke passed its 128-token request,
then failed the finite-logprob assertion in the 127/128/129-token multi-request
batch. With the exact independent #17828 prerequisite, baseline eager smoke
passed. Candidate eager and both graph arms are still pending at this entry.
No custom dummy loader, operator substitute or registration replacement was used.
The waiting diagnostic-v1 controller was intentionally stopped before
any device phase to prioritize queued timing controls in diagnostic-v2; its
termination evidence remains retained. No other task's process was stopped.

Snapshot completed-snapshot-v1.tar contains 275 text files, 24698880 bytes,
SHA256 5a9d19a09b0ede290275be3adf5e9074681db88e79f82b9f5d80a72642699108.
Only terminal experiment directories are included, plus source/configuration
records. Live models and queued diagnostics are not marked complete by it.
All output tensors remain on the cloud with their hashes in the manifest.

## Standard-dummy whole-model functional comparisons completed

Integration controller completed with exit 0. All four fixed model arms passed:
baseline/candidate in eager and FULL_DECODE_ONLY configurations. Each arm uses
four requests, 32 generated tokens and 160 finite logprobs. Tokens and all
logprobs are identical across variants, with maximum difference 0. All four
functional-results.json files share SHA256
9746530c94216c3aa12588656b59c77ecfb6806f720833fbf6507d51c27bafcd.
The fixture configuration SHA256 is
f259aa655d23962ee587ca2c0449867204ae7ad4b1e218fc36865a66765f481e.
Standard DummyModelLoader is used, without bounded-loader or operator overrides.
Both variants use the same exact convolution prerequisite. This is a four-layer
synthetic BF16 functional smoke, not checkpoint accuracy or model throughput.

Startup logs confirm FULL graph capture for sizes 1/2/4. Runtime graph-replay
trace proof is still pending, and no graph speedup is claimed. The model-profile
controller waits behind diagnostic-v2 and then collects both variants using
the original model and standard loader with profiling explicitly enabled.
