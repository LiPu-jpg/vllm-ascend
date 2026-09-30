# HcPre runtime iteration 02 evidence

Runtime source: `d50abbec269b1f55983f122388d608b0fab38a62`.
Latest inspected upstream: `88aebfb2dad70efb5721c1691a91b12f30299b25`;
the intervening changes do not touch HcPre or its GLM callers.

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

## Remaining validation

Standard-dummy BF16 GLM smoke uses the original loader and real four-layer model
with KDA, MLA and mHC. The unpatched baseline passes a single request but fails
finite logprobs in a multi-request batch. The independent causal-convolution
prerequisite from #17828 is applied identically in both comparison arms, in a
private checkout. The completed snapshot includes the unpatched failure;
subsequent completed-model results and comparison are included separately.
Startup confirms graph capture; runtime graph-replay trace proof is pending.

Queued-graph A/A, controlled registration comparisons, tail cases and fresh L1
profiling remain pending in this snapshot. The queued timing hypothesis concerns
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
