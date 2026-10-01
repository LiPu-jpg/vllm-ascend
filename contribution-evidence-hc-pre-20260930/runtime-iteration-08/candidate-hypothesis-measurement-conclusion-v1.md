# Candidate 7: batch HcPre comb input copies

## Hypothesis

The production HcPre comb load submits one CopyIn per Cube partial and token.
Batching those partials inside one CopyIn per matrix row can reduce submission
overhead without changing the valid-element UB layout or reduction order. The
batched path applies when partialCount > hcMult and the public DMA count and
stride limits are representable; the original path remains the fallback. For
example, partialCount=32 and hcMult=4 reduces source API calls per token from
32 to 4. This example is not a measured device tiling or latency result.

This is an independent upstream implementation inspired by competition
multi-matrix batching. It copies no competition source and changes no
arithmetic, epsilons, finite iteration counts, interface, dtype, tiling,
architecture-35 implementation or UB allocation.

Base: 62e05feb3db521230c27714ad4347bd0d9d38f1a.
Candidate: d64140c62797ebddea73b2cf091a3590b4956d99.
Runtime header SHA256:
5d8ef9f6c1955fa7e53ee7071f111d20b0d7b2edac23aa89c38149cb44c87779.

## Measurements completed

- Source address audit: 3,640 geometries, including 1,924 batched-path cases,
  and six API limit checks. All valid-element source/destination mappings and
  destination block coverage checks passed. Padding values were not assumed
  byte-identical; the downstream mask dependency review still requires NPU
  output validation.
- Tracked-file repository `bash format.sh ci`: actual exit 0 after the signed
  source commit; source worktree remains clean.
- Matched private native and OPP builds: both completion markers found, both
  expected source HEADs and clean diffs verified, all eight binary hashes
  verified. Candidate HcPre object SHA256:
  6d61b07369e00128935c280227e9f3033605505b40a912fc2e1bda8c75e5e50d.
  Baseline HcPre object SHA256:
  e4fe3ba278578281a0bb142d5da21cbfeb6d55e355378112fc429440eea23622.
- Build controller exit 1 is retained: foreign task detected after both builds
  completed, so no final all-guards-pass marker or post-build NPU snapshot was
  produced. Terminal product integrity is separate from permission to test.
- Future validation input integrity: 42 iteration files, seven manifests and
  five shared task dependencies verified. This proves preparation integrity,
  not correctness or performance.

The earlier 42 hardware HF32 rounding controls and 56 saved-tensor CPU
sensitivity cases concern the production baseline and candidate 6; they are
reference diagnostics, not candidate 7 correctness or timing measurements.

## Measurements still required

1. In a fresh foreign/device-clean window, verify actual private HcPre kernel
   selection. Run normal production-plugin nightly collection and all fixture,
   exact benchmark-input, optional-output boundary and actual GLM decoder
   method cases. Record the original oracle's failures without counting them
   as passes.
2. Independently record the corrected HF32 reference with six new hardware
   regressions and unchanged error/pass-rate thresholds. Require all 48 real
   fixture and all 28 exact benchmark inputs per arm to pass the CPU gate, with
   eager/graph/input and baseline-byte parity. Also run all 24 generic-width
   cases per arm for hcMult 1, 3 and 8, retaining every numerical failure.
3. Run every planned independent process in graph ABBA, graph AA, graph BAAB,
   event ABBA and event AA order. Retain all 28 cases, three rounds, raw NPU
   events and synchronized host wall samples, including warmups. Graph samples
   contain 640 complete HcPre calls. AA controls never correct a candidate
   speedup ratio and the fastest round is never selected.
4. Profile eager/graph critical paths and verify that the proposed load schedule
   improves observed work. Then run the standard-loader synthetic GLM smoke in
   both modes with the same isolated prerequisite patch on both sources. Keep
   dummy-weight smoke separate from checkpoint accuracy or model throughput.

## Conclusion

The candidate is compiled and ready for production validation once the active
SFA build has completed and a fresh clean window is verified. Source and binary
integrity support executing the experiment; they do not establish a speedup.
The runtime candidate has not executed on NPU yet. Operator gain, stable
performance and model functional integration remain unproved. No runtime PR or
formal review request is justified by the present measurements.
