# HcPre comb input copy batching

Latest NPU status: see
`candidate-npu-original-reference-interrupted-findings-v1.md` and
`continuation-status-v4.json`. Both actual private kernels have executed through
the full plugin. Both arms passed all 48 real-shape fixture cases, while the
original-reference nightly retains 12 failures per arm. The first cohort was
interrupted before the candidate benchmark-input program by a new foreign task;
the remaining phases and every performance measurement are uncompleted. The
separate recovery started after fresh clean guards, as controller PID 1592950;
its results remain pending. The 114 interrupted-cohort
raw text records are retained and their hashes pass locally.

The following compiled-only status is historical, at 2026-09-30 22:59 UTC.
Both matched builds had completed and
their eight binary hashes have been independently verified. The original build
controller PID 1555557 is terminal with exit 1 because the post-build foreign
task guard detected the SFA deferred-build process. Its exit, missing final
completion marker and postguard record are retained. Binary integrity does not
override that failed guard. SFA controller 1568833 subsequently started and was
confirmed live, so no candidate correctness or performance execution has begun.

The fresh read-only device snapshot shows NPU 3/chip 0, 910B3, Health OK, 37 C,
65536 MiB HBM and no NPU processes. The separate foreign-task guard still fails
on the active SFA build; validation must wait for a fresh clean window.

`terminal-build-integrity.json` records base `62e05feb` and candidate `d64140c`
plus every compiled-object hash. `all-staged-inputs-sha256-verified-v4.json`
binds 42 future validation inputs and seven manifests to identical local and
cloud contents, plus five task-owned shared dependencies used for the runner,
device guard, kernel tracer and standard-loader model smoke. The first
preparation documents and manifest revisions are preserved separately.

`candidate-hypothesis-measurement-conclusion-v1.md` records the current runtime
hypothesis and the measurement gates. No operator or model speedup is proved.
No runtime PR has been created. The original 10-bit truncating reference and the
hardware-supported 11-bit nearest-away reference will be recorded separately;
all old numerical failures and original thresholds remain retained. The new
reference regressions have not run on this candidate.

The following is the initial preparation account, preserved in full as
`README.initial-preparation-v1.md`. Its process observations and unbuilt status
are historical and are superseded by the current status above.

## Initial preparation account

Base: vllm-ascend `62e05feb3db521230c27714ad4347bd0d9d38f1a`.
Candidate: `d64140c`, branch `codex/hc-pre-batch-comb-copy-20261001`, local worktree
`/Users/jiaoziang/vllm-ascend-hc-pre-batch-comb-copy-20261001`.
This candidate does not include the previous input-prefetch schedule.

The original comb input loading submits one CopyIn per Cube partial and token,
with hcMult blocks in each call. The candidate exchanges the traversal axes:
one CopyIn per matrix row and token, with cubeBlockDimK blocks. Valid elements
remain in the same partial-major UB layout and preserve reduction order.
The original traversal is retained for fewer partials and API count/stride
limits. No arithmetic, iteration count, epsilon, tiling or arch35 change.

`check_comb_copy_layout.py` independently expands the public DMA units (GM byte
stride and UB 32-byte block stride). All 3,640 geometries passed source and
destination valid-element mapping and destination block coverage checks; 1,924
use the batched path. Six API limit checks passed. This is a source address
model, not a compiled-kernel test. Dummy padding VALUES are not compared, and
NPU output validation is required. The JSON binds the audit to the header SHA.

`bash format.sh ci` completed with exit 0 before the DCO commit. All hook output
is retained in `format-ci.log`. No NPU build or candidate execution has happened.
No operator or model speedup is established. No runtime PR has been created.

Upstream main was rechecked and remains the base above. PR #17054 remains open
at `33bfef419bc4dbe679582011104beca9112373be`; its current diff is retained as
`pr17054.diff`. It batches Sinkhorn column computation and changes tiling, while
the existing comb CopyIn traversal is unchanged. The new batching proposal
touches the same header and will need integration review with that PR.

The competition source is local audited b2-pro commit
`4546d1864b3a16da3fc8bfe5ad3b06de380526bd`, kernel SHA
`69b96af229174a8e25271f147c67f7561ffa4e11c79013988bc531135b076128`.
Its B2_SUMMARY.md records the highest complete receipt 86.926306; two subsequent
same-source receipts were 82.197957 and 79.070630. These are competition scores,
not vLLM throughput gains. The source contains multi-matrix processing and Cast
layout fusion, as well as fast branches with shortened iteration behavior that
cannot be migrated as exact finite-iteration Sinkhorn. No root source license
was found in the audited clone. No competition source code has been copied into
this change; the upstream file's existing CANN OSL v2 header is retained.

SSH recovered during preparation. Fresh foreign_jobs.py observation returned
exit 1 with SFA controller PID 1523840, wrapper PID 1525277 and Python PID 1525400.
npu-smi confirmed NPU 3/chip 0, 910B3, Health OK, 38 C and active Python 1525400.
No new NPU task was started. The previous HF32 rounding diagnostic's pid/log/exit
files were absent at this observation; connection restoration was not treated
as a reason to restart any existing task. Recheck actual processes before any
future build or test. The oracle diagnostic remains necessary for interpreting
known baseline signed-input CPU-reference failures without changing thresholds.
