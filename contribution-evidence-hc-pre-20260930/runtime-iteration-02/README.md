# HcPre runtime iteration 02 evidence

Runtime source: `d50abbec269b1f55983f122388d608b0fab38a62`.
Latest inspected upstream: `143861fd6931e388aa3609b8efd620dd8e3fd252`;
HcPre, its bindings and GLM/DeepSeek V4 caller files are unchanged. Related
GLM helper changes since the original snapshot need final model revalidation.

The candidate seeds an aligned FP32 reduction with its first addition, removing
an initializer copy and preserving the original left-fold arithmetic. Padded
and single-row reductions retain their copy. No competition code is imported,
and the existing CANN OSLA 2.0 header is preserved. PR #17821 remains test-only.

## Completed validation

- Normal nightly: 53/53 on the complete existing plugin, then 53/53 on a fresh
  complete native extension built from exact candidate source.
- Actual GLM decoder methods: baseline 24/24 and candidate 24/24, with eager/graph,
  unchanged CPU-oracle thresholds and baseline bitwise comparison.
- Three fresh diagnostic processes observed the actual baseline/original/peeled
  kernel file opens. Object hashes match their private built packages. These
  diagnostics use LD_PRELOAD; performance measurements do not.
- All 28 cases and every sample from both A/A and candidate ABBA are retained.
  At warmup=500, A/A yields 0.98566 geometric mean, with apparent slowdown up to
  3.78%. Candidate ABBA yields 1.01638, 22 faster and 6 slower, maximum slowdown
  4.30%. These are provisional measurements, not accepted stable gains.
- Earlier concurrency failures, contaminated comparison data, and the failed
  metadata getter are retained rather than overwritten or counted as passes.
- Standard-dummy GLM functional comparison passed in eager and FULL_DECODE_ONLY
  configurations. Each arm generated 32 tokens for four requests, with 160
  finite logprobs. Baseline and candidate tokens/logprobs are exactly identical.
  Both use the same independent convolution prerequisite from #17828.

## Current conclusion: reject this reduction candidate

Queued replay ABBA now yields 0.98385720 geometric mean: 16 faster and 12 slower,
maximum slowdown 8.45%. Both independent process pairs reproduce regressions
for several small batches. Queued A/A yields 0.99941293 but still has per-case
variability, including apparent gains up to 5.43% and slowdowns up to 2.28%.
All samples and failures are retained. The earlier 1.01638 result is insufficient
to accept this candidate.

Matched original-candidate registration controls yield 1.00187839 in production
and 1.00848297 in the historical probe, with 16 faster and 12 slower in both.
Configuration, kernel paths/hashes and runtime options are recorded. These do
not reproduce the old fixed production advantage. An external event submission
gap was observed, and A/A shows substantial variability; no single cause of
the historical difference has been proved. The historical 1.04412 result is
not accepted performance evidence.

All 42 operator profile cases include 60 HcPre observations. Small-batch
regressions also appear in kernel durations. For eager t4/d7168, baseline/original/
peeled median durations are 30.921/32.5605/35.281 microseconds; AIV scalar durations
are 5.592/6.690/6.4525 microseconds. Counters support an overhead regression,
but the installed disassembler cannot decode the instruction set, so the exact
scalar instruction cause is unproved. Profiled timings are diagnostic and are
not pooled into benchmark samples.

Tail diagnostics retain 27/120 CPU-oracle failures in both baseline and candidate,
plus 12 candidate cross-process byte-parity failures at hidden=7169. A fresh
identical-baseline run passes 117/120 CPU cases and differs from its first run
in all 24 hidden=7169 cases. This establishes baseline tail instability under
these conditions, not candidate correctness. Failures are not reclassified as
passes or removed from evidence.

Actual standard-dummy model traces now prove runtime graph execution: each
variant records 14 aclmdlRIExecuteAsync events, 24 eager HcPre kernels and 112
HcPre kernels with graph model IDs 47/48/49. Tokens and finite logprobs still
match across the four earlier functional arms. This proves graph integration,
not model throughput improvement.

A separate optional-output V2 candidate is being investigated on its own branch.
Its correctness and performance are not established by this reduction evidence.

## Model prerequisites and scope

Standard-dummy BF16 GLM smoke uses the original loader and real four-layer model
with KDA, MLA and mHC. The unpatched baseline passes a single request but fails
finite logprobs in a multi-request batch. The independent causal-convolution
prerequisite from #17828 is applied identically in both comparison arms, in a
private checkout. The completed snapshot includes the unpatched failure;
subsequent completed-model results and comparison are included separately.
Startup and the completed runtime traces confirm graph execution.

The completed-diagnostics-v2 directory retains the queued controls, matched
registration comparisons, tails, all 42 L1 operator cases and both model traces.
The queued timing hypothesis concerns
the external event-to-host-submit gap; it has not been established as the cause
of historical discrepancies. Operator timings do not establish model throughput.

See [journal.md](journal.md), [A/A results](idle2-aa-summary.json),
[candidate results](idle2-peeled-summary.json) and the raw iteration directories.
The archive contains terminal experiment directories only. Output tensors and
profiler binary data remain on the cloud with hashes in the manifest.

Snapshot: 24,698,880 bytes, 275 text files; SHA256
`5a9d19a09b0ede290275be3adf5e9074681db88e79f82b9f5d80a72642699108`.
The fork-only archive branch excludes the evidence directory from automatic
formatters to preserve raw checksums. The actual source contribution uses the
unmodified repository lint configuration and passed `bash format.sh ci`.

The diagnostic snapshot has 1,323 text files, 64,614,400 bytes; SHA256
`37ce4add7f04611f44dded6bd6644480562f1a40775ce25d6a437617d909a13b`.
Binary profiler and tensor files remain on the cloud with manifest hashes.
The additional baseline A/A tail result is included separately.
