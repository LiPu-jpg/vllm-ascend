# Short-vector Div evidence, current status

Baseline a40b52df0ef06a6360e2e97ce9b37a8939240d3f, runtime candidate
21d7920f51a71cedd1500ac95929d44031cbaafd. No stable benefit established.
PR17821 still contains only tests, benchmark and documentation.

All28 cases and every measured sample are retained. Graph ABBA geometric
mean speedup0.995288552144213 (10faster18slower,max slowdown4.055678%).
Reverse BAAB0.9877529453485497 (5faster23slower,max slowdown5.484968%).
Same-code graph A/A0.9630107639854758. Event ABBA1.067104549743223 has
pair means1.0073294452127934/1.1052490067848808; event A/A0.9752871222094138.
No A/A correction, selective round or model-throughput claim is made.

Each normal nightly arm passes65/77 and fails the same12 cases. A separate
all-output diagnostic retains all72 fixtures:60 pass each, all48 real hidden
4096/7168 fixtures pass CPU and byte-parity checks; the12 hidden128 failures
remain failures. Boundary each57/60 CPU pass; candidate6 cross-process
parity-error cases remain. Actual GLM decoder-method24 checks pass each.

V9 controller1427028 is terminal0 with all recovered controls completed.
V7 exit1 and its foreign-after failure remain; the interrupted old A/A arm is
not counted as a clean cohort. V10 controller1468225 is terminal exit1. All four L1 arms completed with
60 HcPre kernels per case:28 retained profile records. All7 graph-profile
Durations increase by3.02% to11.53%; vector busy time changes by at most
about0.36% in those graph diagnostics. These are diagnostics, not benchmark
samples or emitted-instruction proof. No critical-path gain is established.

The standard DummyModelLoader smoke produced8 requests,64 generated tokens
and320 finite logprobs per arm in eager and graph modes, with exact tokens and
maximum logprob difference0. Graph traces show14 aclmdlRIExecuteAsync events
and112 graph HcPre kernels plus24 eager kernels per arm. Both private sources
use the same independent17828 packed-convolution prerequisite. Eager arm
guards pass. Candidate graph run.exit1 retains a foreign-after failure: SFA
controller1479427 appeared after the before-check. Functional results do not
turn that failed guard into a clean cohort. Original logs/statuses are unchanged.
No trained-checkpoint accuracy or model-throughput gain is claimed.

The short-vector Div candidate is rejected for upstream latency optimization.
The independent input-prefetch source b8f067cd3f01c78fc2e7d35f12385a948dac1a26
has93 expected nightly cases and a separate28 benchmark-input CPU diagnostic,
but no NPU build/test/timing outcome yet. Other candidate runtime changes are
not stacked. Historical journals retain prior states.

Original logs, tests, guards, commands and raw text files are preserved byte
for byte. Binary tensors and packages stay in the private cloud workspace.
The12 scanner findings are upstream SHA256 build-cache identifiers, audited
in cache-fingerprint-audit.json and narrowly allowed by exact fingerprints
in this evidence branch's .gitleaksignore. No scanner rule is globally disabled.
