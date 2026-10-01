# Comb-copy batching: completed correctness records and unresolved tails

This is supporting evidence for a runtime candidate, not a completed performance
contribution. No timing, profiling or standard-loader model smoke has executed
for this candidate. No operator or model speedup is established.

Base: `62e05feb3db521230c27714ad4347bd0d9d38f1a`.
Runtime candidate: `d64140c62797ebddea73b2cf091a3590b4956d99`.
The candidate groups comb input copies across Cube partials while retaining
valid-element UB layout, reduction order and the original API-limit fallback.
It was independently implemented without copying competition source.

## Executed production-plugin coverage

Both private native extensions and OPP packages completed building; all eight
binary hashes were verified. The original build controller nevertheless exited
1 when its post-build guard detected another task. That failed status and the
absence of a final all-guards-pass build marker remain retained. Separate clean
windows were required for subsequent NPU execution.

Actual private HcPre object opens were verified on Ascend 910B3 device 3.
All twelve corrected-reference phases passed the device and task postguards.
Normal nightly collection used the real repository conftests and dependencies.
There are no loader replacements, mock registrations or skipped dependencies.

| Corrected-reference coverage per arm | Baseline | Candidate | Limit |
| --- | ---: | ---: | --- |
| Nightly | 87/99 pass | 87/99 pass | Same 12 small-hidden failures retained |
| New HF32 midpoint regressions, included above | 6/6 pass | 6/6 pass | Verified 910B3; other architectures unverified |
| Finite fixtures | 60/72 CPU pass | 60/72 CPU pass | All 48 real-shape cases pass; 12 h128 failures |
| Exact benchmark inputs | 28/28 CPU pass | 28/28 CPU pass | No timing recorded |
| Boundary inputs | 48/60 CPU pass | 48/60 CPU pass | All 12 hidden=7169 cases fail CPU checks |
| Actual GLM decoder-method calls | 24/24 pass | 24/24 pass | Six CPU checks plus eager/graph checks per case |

The candidate additionally differs from baseline bytes in six token=1,
hidden=7169 boundary cases: positive/signed inputs times 1/3/20 iterations.
These differences remain unresolved and prevent accepting the candidate as
fully validated. Neither matching failure counts nor successful recording
controller exits turn failed numerical cases into passes.

The original-reference recovery is also retained. It records 81/93 nightly
passes, 60/72 finite-fixture CPU passes, 16/28 exact-benchmark CPU passes,
45/60 boundary CPU passes and 24/24 decoder-method passes per arm. Original
thresholds were unchanged. The corrected A2/A3 reference uses the separately
hardware-validated 11-bit nearest-away HF32 conversion; A5 retains its prior
reference and is unverified here. Current corrected-reference source is
signed commit `e4ccfa6e4edf5e687190abbd0a1670ca52ac4c4a`; its runtime matches
the candidate above. Older failed-reference results have not been overwritten.

The extra hc_mult=1/3/8 diagnostic failed with controller exit 1: all 24 inputs
per arm were rejected identically by the actual native hc_mult=4 contract.
The separate source-and-record classification retains that failed controller
and comparator, supplies zero positive generic-width coverage, and does not
widen the production API.

## Tail investigation

CPU analysis of 60 saved baseline outputs from two completed NPU runs verified
matching input hashes, saved-tensor hashes and identical output bytes in every
case. Those boundary saves contain no CPU golden tensors. This is no new NPU
execution and does not excuse candidate differences as baseline variation.
The first analysis invocation incorrectly expected saved golden tensors and
failed with KeyError; its script, log and exit 1 are retained alongside the
completed output-only comparison.

Static inspection verifies identical 9,056-byte Cube instruction bodies and
identical Cube relocations in both compiled objects. Vector bodies and some
Vector relocation offsets differ. The raw LLVM disassembly returned
`<not available>` instead of decoded instructions; its exit 0 does not provide
decoded instruction evidence. Cube byte/relocation comparison is separate.

The current source loads the actual K tail but still uses K=32 in the final
matrix multiply. A four-element tail can therefore raise a padding/state
dependency question; this is a hypothesis, not a demonstrated root cause.
The supported A2/A3 [Mmad Basic API](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/cube_compute_ISASI/mmad_compute/Mmad.md)
describes K as the matrix dimension and default float K layout alignment to 8.
The experimental Tensor API for 950 does not establish A2 behavior.

A 64-case-per-arm production diagnostic is staged to vary valid preceding
calls, check fixed-input history dependence, repeated calls, graph replay and
external pre_mix. It has **not executed**. Input hashes bind its prepared
scripts. The latest device snapshot was idle, but a foreign compilation task
was live and the task guard returned 1, so no diagnostic or timing was started.

## Reproduction and integrity

`terminal-source7-correctness-text-v1` freezes 364 completed text records.
`interrupted-original-reference-text-v1` preserves the first interrupted cohort,
including its failed foreign-task guard. The separate reproduction supplement
retains the nightly XMLs, frozen source/bundle, manifests, exact validation
scripts, original controller exits and prepared future scripts. Static compiled
inspection records are stored separately. All existing manifests were verified
against their copied files before adding this archive.

Use the recorded revisions, environment, build commands and guarded scripts
under the original task root. Paths are machine-specific. Inspect actual device
and process state before launch, and inspect a timed-out controller's PID, log
and exit before retrying. The unexecuted performance starter still requires a
successful generic-width diagnostic; that dependency is inappropriate to the
native hc_mult=4 contract and needs an explicit replacement, not changing the
retained generic failure to success. Tail correctness remains unresolved.

Run `python verify_archive.py` here to verify every published file against the
archive inventory. Full build outputs and tensor files remain on the cloud,
with their hashes in the records. Archive integrity does not certify numerical
correctness, performance, or completion of the contribution goal.

The separate redacted archive scan initially identified twelve `key=` values
in the original build log. Source inspection verifies these are SHA256 build
cache identities. Their exact file/line fingerprints are listed in the local
`.gitleaksignore`, with the source mapping in
`build-cache-scan-false-positives.json`. The raw log stays unchanged, no global
rule is disabled, and the scan with these specific exclusions passes.
