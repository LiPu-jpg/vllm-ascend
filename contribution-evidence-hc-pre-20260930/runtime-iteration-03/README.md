# Optional V2 output: allocation reduction, no stable latency gain

The independent candidate omits the unused V2 `pre` tensor using the kernel's
existing optional-output contract. V3 retains all four outputs. Baseline is
`eee0ef7dfbe99a7ada56dafb3739dd952a0265b5`; candidate is
`2ca077784546fbc5455ec42cd9c82ceed2b4a6a0` (see revisions/manifests for exact refs).
Both variants use the same HcPre kernel binary. No competition source is copied.

Graph ABBA geometric mean 1.026566, BAAB 1.005557, graph A/A 1.008365;
eager ABBA 0.998681, eager A/A 1.106062. The 10.6% apparent same-code gain
demonstrates measurement variation. Allocation reduction is real: eager L1
traces show four instead of five `empty_tensor` events per call including
workspace. Stable operator latency improvement is not established. All seven
graph profiled kernel medians regress; diagnostics are separate from benchmarks.
This candidate is excluded from PR #17821 and does not complete the optimization.

Normal nightly passes 41/41 per arm; actual decoder checks pass 24/24 per arm.
Tail tests retain 15/60 CPU failures per arm and six candidate cross-process
parity failures at t1/d7169. Failures are not reclassified as passes.
Standard DummyModelLoader GLM functional tests match, using the same independent
convolution prerequisite from #17828. The later actual model profiles compare
eight requests, 64 tokens and 320 finite logprobs per arm, maximum difference 0.
Both traces prove 14 aclmdlRIExecuteAsync events, 112 graph HcPre kernels and
24 eager kernels. No trained-checkpoint accuracy or model throughput is claimed.

See [journal.md](journal.md), all comparison summaries, raw samples and traces,
and [actual-model-profile-summary.json](actual-model-profile-summary.json).
The archive retains earlier failures, all slowdowns and every measured sample.
Output tensors and binary profiler files remain on the cloud; published text
files are hashed in `published-file-manifest.json`.
