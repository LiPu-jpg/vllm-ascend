# SFA padding optimization: withdrawn after three candidates

Decision: reject the current padding optimization as an upstream performance contribution. It does not remove observed regressions; original/current native implementation remains the target. Do not interpret these experiments as whole-model speedup.

## Iteration history

|Round|Mechanism|Lower/higher device medians (all52)|Best reduction|Worst slowdown|Decision|
|---|---|---|---|---|---|
|1|Coalesce key+RoPE copies; larger UB zero clear|20/32|6.91%|3.39%|Rejected|
|2|Only RoPE copies, reuse original zeroed key row|32/20|7.33%|3.39%|Withdrawn; mixed benefit/regressions|
|3|Element offsets, full chunks and one short tail, no row-count division|11/41|3.26%|6.84%|Rejected|

## Complete third-round evidence

All52 identical nonempty cases, B/C/C/B/B/C process order; three independent processes and 15 raw event and amortized wall samples per case/build. Current native serves as baseline and target; no synthetic slow reference. [Full52 table including ranges and wall samples](performance-table.md), [all per-process medians/raw observations](performance-summary.json), [independent profiler52/build](profiler-comparison.md). Wall medians decrease in 36 cases and increase in16; they are amortized dispatch-inclusive values, not single-call or model throughput.

The fresh unchanged-source build uses the same compiler, flags and build wrapper as round3. All four artifact SHA256 values (two objects/two descriptors) match the previously preserved baseline exactly. [Identical-binary control all52](build-control-table.md) is a separate one-process/installation comparison: observed deltas range -2.315% to +3.516%. This is not a bound on all future variation or a significance test.

Round3 cases with each candidate process median greater than every baseline process median: 2, 5, 8, 9, 11, 24, 26, 27, 28, 29, 30, 31, 42, 44. This describes the observed three-process ranges; no statistical significance or single causal attribution is asserted. Case2 has +6.843% in acceptance, compared with +0.509% in the separate identical-binary control; case23 remains +3.186%.

A2 extra public-script runs reproduced higher medians for cases1/17/23/29; case40 reversed direction in the final extra run. All those measurements remain preserved. RoPE and NoPE share V-template code; source-unaffected paths are required controls. ELF V-template AIV function sizes grow by104--272 bytes in round2 and172--288 bytes in round3; removing one division did not shrink the whole emitted function. These observations do not prove the cause of each timing difference.

## Correctness and operational records

Both third candidate and rebuilt original: 56/56 native pytest, 60 numerical/byte-parity cases, 80 actual DCP-remap/device-dispatch component cases. Expanded coverage retains all96 layout/block/mode/head cases plus2 actual dispatch checks, with byte-identical baseline outputs. Eight existing BSND/block8/head1 nonempty LSE failures remain failures in both builds; generic near-zero MERE/MARE criteria are not claimed to pass. Project attention tolerances and FP64 references are retained. No full distributed DCP/model inference or physical A3 validation.

The controller ended0, both profiler datasets complete52 cases. Baseline paired-b3 attempt1 detected external PID1377648 before first case, exited75, retained log/exit; the next attempt waited for the external controller and ran from a fresh output path. No external process or environment was modified. Both accepted B3 and all other acceptance datasets complete52 cases.

Source candidate commit32329062a0c4faa9eeb92d806e893aea7bf875c0, source headerSHA25680cbbcddc11d4ae5fbf344a53642fc22a8530e2bd3745665745a19126b2ce5ce. Unchanged-source control base11682d1e341d161a4129a58863f39a912846f71d. Shared host/framework libraries are identical, private packages/isolated worktrees only. Raw archiveSHA256c1ec9d217ed762524e970fc7ee1c55a0b0d10073fc0cf01366852eff77a2386b; all290 recorded file hashes verified after transfer. Raw binary profiles/tensor references and full source archives remain in the private cloud experiment workspace. Independent source patch/scripts are supplied separately. No contest code is copied.

## Findings

1. Reduced RoPE padding DMA can help short valid prefixes; the benefit does not establish stable improvement across the actual supported workload matrix.
2. Code changes can affect shared compiled paths even when a particular runtime branch is skipped; both NoPE and fully populated tiles must remain visible.
3. Rebuilding the original produces identical artifacts, and those artifacts still exhibit process/device variation. Variance does not justify deleting reproducible negative observations.
4. The third candidate worsens the all52 matrix and independent profiler result; this route is withdrawn, not promoted on its fastest cases.

Reproduce with the frozen52 JSONL and existing paired.py/profiler.py/test_helper.py from ../probes. New build/install/controller scripts are in ../reassessment-20260930. Directory a3 denotes iteration3, not Ascend A3 hardware.

Frozen source: [32329062](https://github.com/LiPu-jpg/vllm-ascend/tree/32329062a0c4faa9eeb92d806e893aea7bf875c0). The source is a rejected experiment; no performance acceptance is implied by publication.
