# Small-query NoPE SFA evidence

Executed source integration: `7f5fb60ea4eebc9fa02915764123a0a1aa17627a`, tested against upstream `62e05feb3db521230c27714ad4347bd0d9d38f1a`. The source PR is now rebased onto `a8fcedb` at `90d996d244bbf1521afb4999ea360325c3021dbb`; all 24 native files and all six changed PR files are byte-identical to executed copies. [Rebase identity](review/rebased-source-identity.json). The all-file formatting check passed again. [Source branch](https://github.com/LiPu-jpg/vllm-ascend/tree/codex/sfa-small-query-workspace-20261001). Nine host-tiling lines bound launch and scratch allocation by tensor rows. Original kernel binaries are unchanged. The three source commits have DCO Signed-off-by; final all-file formatting passed.

Latest upstream reviewed: `a8fcedb03d93e60efceddbfc912406f7fa491d57`. Its only additional commit moves CI scripts/configs; SFA native source, dispatcher and all changed PR paths match the tested base. Related PR #17653 remains open and changes A3 valid-prefix kernel work rather than this host launch rule. Physical A3 and their combination remain unverified.

## Outcomes and limits

The public benchmark uses actual native/quantized Indexer output order on synthetic features and unquantized NoPE SFA. It captures once and replays the same 40 inputs in separate original/candidate processes. Both orders, every case and all five raw timing samples per process are retained. [All 40 case comparisons](public-case-comparison.csv) include both rounds, process medians and memory reductions.

- Forward B/C/C/B: 18 lower, 22 higher; largest increase 1.7883%.
- Reverse C/B/B/C: 30 lower, 10 higher; largest increase 1.2230%.
- Query counts 1/2/4/8: all 16 cases lower in both orders, reductions 4.6473–7.8103% across those rounds. Count 16 is mixed in forward and lower in reverse. Larger controls remain in both reports. Order-dependent differences are observations; no causality or noise explanation is established.
- Original / launch-only / combined memory: eager and graph peak-increase reductions at counts 1/2/4/8/16 are respectively 57,796,096 / 65,135,104 / 58,818,560 / 44,113,920 / 14,704,640 bytes. Counts 20/21/24/25/32 match. Original and launch-only match across all 40 cases. Single-query reduction is 55.1187 MiB.
- Final combined E2 expanded performance: all 364 cases retained, 234 lower and 130 higher; maximum increase 3.8763% in a RoPE64 control outside the guard. The 192 boundary cases include 124 lower / 68 higher; the 172 retained cases include 110 lower / 62 higher. Boundary counts 2/4/9/10/11/12/13 have all 112 cases lower; counts 16/19 retain increases up to 1.6975% inside the bound.

These are SFA component/device latency and Torch allocator observations. They do not establish model latency/throughput, model memory or device-wide HBM savings. Clocks and power were not fixed. No statistical-significance claim is made. Only one physical A2 (910B3, 20 AIC / 40 AIV, CANN 9.1.0) was tested. Physical A3, distributed execution and whole models remain unverified.

## Correctness scope

Both builds passed **418 submitted public tests** (402 active-core/head tests + 16 workspace/graph tests) and **198 retained private tests**. The latter are supplementary tests, not upstream-existing tests and not additional source files in the PR. Earlier historical notes referring to “public616” require this corrected split. Public file hashes and JUnit counts were verified.

All 192 boundary checks passed their numerical reference per build. Only the 96 LSE-disabled cases exercise production dispatcher byte parity; the other 96 are LSE diagnostics. The legacy boolean `production_dispatcher_byte_parity=false` on LSE-enabled rows means that comparison was not exercised.

Broader legacy probes are **not all numerical passes**:

- Eight BSND/block8 nonempty LSE failures and 20 partial-block reference failures are freshly reproduced on the original. Their error records are retained.
- Twenty block8/head1 cases differ in empty attention output: original NaN versus candidate Inf. Both are invalid. Every nonempty output and every maximum/total statistic is byte-identical; repeated calls within each diagnostic process match. These cases are outside the optimization guard. Do not claim complete legacy output byte parity.
- Ten large-index configurations were considered per build. Six execute, pass their reference and match original bytes. Four optional-length/block2/4 original calls are rejected; their candidate replay lacks an original capture and was not executed. These four are not passes.

The strict audit's original failed attempts and subsequent schema corrections are retained. [Final audit](raw/reference-and-diagnostics/iteration-e2/acceptance-v1/final-expanded-audit-v6.json) explicitly records `all_legacy_numerical_cases_passed=false`. No error was converted into a numerical pass.

## Provenance and raw records

`raw/e1-initial`, `raw/e1-expanded` and `raw/e2-initial` are earlier separate experiments. The old E1 compatibility-only installation did not execute the intended fresh host and cannot support an optimization claim; see [installation audit](review/installation-audit-20261001.md). Corrected host identity is checked via the actual rt2.0 library, not merely the compatibility entry. Actual profiler counts include single-query 1 AIC / 2 AIV and query-count32 20 AIC / 40 AIV.

Final records are in `raw/e2-expanded`, `raw/public-forward`, `raw/public-reverse`, `raw/final-pytest` and `raw/reference-and-diagnostics`. The current runtime audit rechecked 512 artifacts; only the intended host library differs. Native source hashes match the compiled snapshot. Every case, slowdown, raw sample, failure, JUnit, mapping and exit record included in these text archives is retained. `export-sha256.json` fingerprints every exported data file.

No recovered competition kernel source or binary is included. The upstream change was independently written against upstream source; existing notices are retained in the source branch.

## Reproduce

Use the standalone benchmark and guide in the source branch, a rebuilt original and candidate installation, matching software/compiler flags and one idle NPU. Capture once using the full custom-op package, then replay unchanged files B/C/C/B and C/B/B/C with fresh processes. Measure memory separately. Preserve all results and audit the actual host library. The guide describes the commands, graph padding, frozen inputs and reporting requirements.

Original input tensors and diagnostic tensor snapshots remain in the cloud workspace and are not part of this text export. Records retain their hashes. Regeneration followed by freezing is a reproducible comparison method; it does not guarantee identical Indexer tie order or serialized `.pt` bytes across hardware/runtime versions. The primary 40-case method is standalone. Retained development harnesses and analysis tools are included for reviewing/reproducing supplemental probes; their installation paths must be adapted.
