# HcPre runtime optimization iteration 01

The performance goal remains incomplete. PR #17821 is still test-only at
52c8d05cba1b3b40999dbe473030ed3d29045561.

## Verified state

- Upstream main: e86df700993c6a83a17306e1320723db86f04691.
- Competition HEAD: 4546d1864b3a16da3fc8bfe5ad3b06de380526bd; no tracked LICENSE.
  No competition source was copied or translated. Only the generic mechanism
  of reducing vector setup/copy overhead is considered.
- Active batch-Sinkhorn PR #17054: 33bfef419bc4dbe679582011104beca9112373be.
  This candidate targets the generic A/R/A reduction, preserving the padded
  n=4 Sinkhorn path; it does not implement batched Sinkhorn.
- Device rechecked: physical NPU 3, Ascend 910B3, logical device 0.
- Existing FLA installation completed successfully. No dependency stub was used.
- Normal nightly baseline: 53 passed in 9.30s; related UT: 4 passed in 0.19s.

## Hypothesis / measurement / conclusion: original candidate

Hypothesis: seed the FP32 accumulator from the first Add to remove a local copy.
The original candidate also adds an accumulator-selection condition in the inner
loop. Historical standalone and full-plugin graph results disagree (1.00351 vs
1.04412 geometric mean); neither is accepted as stable performance evidence.

Two fresh L1 profiling collections contain all 60 expected HcPre kernels per case.
The first collection warns about stopping in RECORD; a second collection fixes
its schedule and preserves the original warnings. Both graph collections lack
ACL-to-NPU flow association because the graph was captured before profiling;
kernel durations/counters are available, but these traces cannot establish host
flow or complete model timing. Profiling overhead means counters are diagnostic,
not substitutes for unprofiled fair timings.

Preliminary counters: original candidate lowers vector work for t512/d7168
(~81.1 -> 79.8us) but raises scalar work (~56 -> 62us). At t1/d4096 it shortens
kernel time. Queue levels 0/1 do not remove the tradeoff; official TASK_QUEUE_ENABLE
has default 1, so an unset historical value does not by itself explain the result.
No causal conclusion about the historical discrepancy is made yet.

## Hypothesis / measurement / conclusion: peeled candidate

Hypothesis: peel the first addition outside the reduction loop, removing the copy
without repeatedly selecting the first accumulator. Preserve the FP32 left fold,
all interfaces/dtypes/finite Sinkhorn iterations, single-row copying and padded
copying. Source change is confined to ReduceSumARAPerf in hc_pre_base.h.

Private build exited 0. Actual kernel object hash:
9bc11fd1d998ed70d1bfd7a4389cab2a8ff28bfb232f763a2b3796a6c6796cfa.
Normal nightly candidate: 53 passed in 9.26s. Required format.sh ci passed.
Performance, actual decoder methods, complete model smoke and tail coverage remain
unverified. This runtime change has not been added to PR #17821.

## Scheduling interference retained

After the candidate nightly, another task's model validation started on the same
NPU (VLLMEngineCore PID 1055706 then 1057440, parent run_model_comparison_v32.sh).
Both decoder-method launches exited at the idle guard before any test ran. A/A
arm aa-a1 completed while this independent sequence was active, so it is excluded
from fair performance conclusions even if its immediate before/after guards were
idle. aa-b1 exited at its idle guard. Our controller PID 1054159 was stopped,
then terminated; the other task and its source/environment were not modified.
All failed guards and the potentially affected data are retained. A fresh sequence
must wait for the known competing controller to exit and use fresh result labels.

Local runtime candidate commit: d50abbec269b1f55983f122388d608b0fab38a62,
on codex/hc-pre-vector-reduction-20260930. Header SHA256
8aa02fbcf5ca137d03168199b48870b4d330a56563adcdfe66abe5ce45ffefaf
is identical to the private built header. The candidate is not in #17821.

The first scheduling retry also stopped at its idle guard during residual
EngineCore teardown. A later guard detected a separate mhc_expand profiling
sequence; it checks other actual shared-environment jobs and requires four
consecutive idle device samples before starting. Queued scripts are included
for reproducibility but are not claimed to have run.

Text snapshot SHA256:
4ed137865175fc6256d74e046073df2a7d37cbe95fefea9ae0231bece55b49c5.
The cloud snapshot manifest records every retained binary/tensor file by hash;
CSV, logs, metadata, XML and scripts are public under raw/. Full profiler binary
and tensor files remain in the task private cloud directory. Historical data
from both previous measurements are still published separately.
