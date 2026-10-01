# Candidate 7: first production NPU validation, interrupted

Update at 2026-09-30 23:35 UTC: the SFA task ended, fresh foreign and device
guards passed, and the separate recovery controller PID 1592950 started. It is
confirmed live, with no terminal exit yet. Its outcomes remain pending. The
original controller's exit 1 and all records described below remain unchanged.

Base `62e05feb3db521230c27714ad4347bd0d9d38f1a`, runtime candidate
`d64140c62797ebddea73b2cf091a3590b4956d99`. The original-reference controller
PID 1570612 is terminal with exit 1. No performance, profiling or full-model
smoke measurement has started for this candidate.

## Hypothesis

Batching comb input copies across Cube partials should retain valid output
bytes while reducing copy submission overhead. Correctness and actual kernel
selection must be established before measuring any gain.

## Measurements

- The fresh prelaunch snapshot identified NPU 3/chip 0, 910B3, Health OK,
  37 C, 65536 MiB HBM, no NPU processes and an empty foreign-task list.
- The full production plugin opened the actual baseline HcPre object with
  SHA256 e4fe3ba278578281a0bb142d5da21cbfeb6d55e355378112fc429440eea23622
  and candidate object with SHA256
  6d61b07369e00128935c280227e9f3033605505b40a912fc2e1bda8c75e5e50d.
  Both tracing processes exited 0 and all four postguards were 0. The tracer
  was confined to these separate diagnostic processes.
- Normal nightly collection completed 93 cases per arm: 81 passed, 12 failed,
  no skips. The failure bitmaps match. All 12 failures have hidden size 128
  and multiple input rows; these failures are retained and are not passes.
- Fixture diagnostics completed 72 cases per arm: 60 passed the original CPU
  accuracy gate, 12 failed it, and those 12 tiny-hidden fixture cases also have
  repeat/V2-V3/graph errors. The recorded nonfinite outputs and errors remain
  in the raw JSON. No candidate-vs-baseline byte mismatch was recorded.
  All 48 cases with hidden size 4096 or 7168 passed the unchanged CPU gate
  and had no repeat/V2-V3/graph/input or cross-arm byte errors. All phase
  postguards were 0.
- The exact 28 benchmark inputs completed on the baseline only: 16 passed
  the original CPU gate, 12 failed it. All repeat/V2-V3/graph/input checks
  passed and all postguards were 0. These original-reference failures are
  preserved independently of the earlier HF32 rounding diagnostics.
- The candidate benchmark-input program did not execute: a new SFA deferred
  process appeared at the prelaunch guard. Its result directory contains no
  results JSON or program log, and the foreign-task guard is 1. The controller
  stopped there; boundary and decoder-method phases were not reached.

114 raw text files were copied byte-for-byte into
`interrupted-original-reference-text-v1`, including the controller exit/log,
normal pytest XML/logs, complete fixture results and guard records. Its internal
SHA256 manifest passes locally. Saved tensor files remain in their original
cloud directories with the per-case digests recorded by the programs.

## Conclusion and next experiment

Actual kernel selection and the 48 real-shape fixture cases support the copy
layout expectation. This is a partial correctness result, not a complete
correctness pass or a performance claim. The interrupted candidate benchmark
arm and the unexecuted boundary/caller phases provide no evidence.

A separate full original-reference cohort is prepared with unique
`batch-comb0r`/`batch-comb1r` labels and controller
`controller-v2r-original-reference`; the original failed controller is never
overwritten. This rerun is justified by the failed foreign-task guard and
incomplete cohort. Its input hashes are verified locally and on the cloud.
The corrected-reference stage now requires that separate cohort to finish
with all guards passing; the original exit 1 remains an explicit prerequisite
record, not a result that is changed to green.

During recovery preparation, SFA controller PID 1572344 was confirmed live and
its screening runners were changing. Its subsequent terminal state and the
new clean device/task window were verified before the recovery launch. After full
correctness recording, require the corrected-reference strict 48-real/28-exact
CPU gate before any timing, including all signed inputs and failures.
