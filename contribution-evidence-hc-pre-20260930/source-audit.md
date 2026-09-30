# Source and contribution audit

Audit date: 2026-09-30 (Asia/Shanghai).

## Fixed sources

- Competition source: `git@git.yinmo.site:ngtibo/b2-pro.git`, HEAD
  `4546d1864b3a16da3fc8bfe5ad3b06de380526bd`.
- Entry: `code/op_host/mhc_sinkhorn.cpp`; device:
  `code/op_kernel/mhc_sinkhorn.cpp`, SHA256
  `69b96af229174a8e25271f147c67f7561ffa4e11c79013988bc531135b076128`.
- The competition repository has no tracked LICENSE or AGENTS.md. The kernel
  does not declare an independent source license. Its seven-file scaffolding
  matches the competition template. Ownership of all template/SDK fragments
  cannot be inferred from possession of the repository.
- No competition source is imported, copied, translated, or relicensed here.
  The transferable observation is to reduce instruction/setup overhead while
  retaining finite-iteration FP32 semantics. Competition FP16 approximations,
  early exit, and shape-specialized fast modes are excluded.
- Upstream tested revision:
  `12fd3a90a0895aebbc58926334e9891683c00699` (fetched 2026-09-30).
  A later fetched `69454b0` makes no changes in the target operator or test.
- GitHub file-history API identifies existing `hc_pre_base.h` introduction as
  `55edd9f6635b67bfc8d395b4f0220418f8acee67`, PR #9271.
  The existing file declares CANN Open Software License Agreement 2.0;
  that header is preserved. Repository-level Apache-2.0 is not substituted for
  the existing file's explicit license. Test/benchmark additions are original
  Apache-2.0 contribution code; the adapter's BSD header is preserved in probes.

## Real callers and overlap

- `vllm_ascend/models/glm5next/model.py::hc_pre` calls `npu_hc_pre_v2`.
  PR #16321 merged that integration, including real GLM A3 correctness and
  smoke evidence without claiming full-model acceleration.
- `vllm_ascend/models/deepseek_v4/model.py` and
  `vllm_ascend/models/deepseek_v41/model.py` call the same fused HcPre family.
- `csrc/torch_binding.cpp::run_hc_pre_fusion` invokes `aclnnHcPre`.
  `hc_pre.cpp` routes A2/A3 to `hc_pre_m_k_split_core.h`; A5 uses separate arch35
  code and is unaffected.
- `ReduceSumARAPerf` reduces stage-one partial sums and contracted stream
  outputs. Complete aligned rows can seed the accumulator with the first Add,
  preserving left-fold order and every padded lane of the fallback path.
- PR #12896 removed the unused standalone `hc_pre_sinkhorn` operator;
  resurrecting it without new runtime callers would duplicate obsolete code.
- Open PR #17054 batches Sinkhorn column stages and fixes column epsilon.
  Its diff does not change `ReduceSumARAPerf`; this contribution deliberately
  retains the unaligned `dim2=4` column path. No batch tiling changes are made.
- Open PR #15429 provides fused mHC Python dispatch; merged #16321 already
  provides GLM native integration. Neither is duplicated.
- Existing user draft #17775 targets mHC expansion; separate branch/worktree
  and private OPP packages avoid modifying that work.
- Another active chat targets SFA; this task does not modify its files, jobs,
  build directories or worktree.

## Validation policy

- Actual discovered device: Ascend 910B3, physical NPU 3, one logical NPU 0.
  Historical device 6 is not assumed to be current.
- Existing runtime reused read-only: CANN 9.1.0,
  torch 2.10.0+cpu / torch_npu 2.10.0.post4. No package installation, shared
  source edits or global environment changes are performed by this task.
- Packages built from the same frozen source and patch, with identical flags
  and separate vendors, under `/mnt/workspace/hc-pre-reduction-20260930`.
- Standalone extension extracts unchanged HcPre allocation, checking and ACLNN
  binding functions from upstream. It replaces only full-plugin loader checks
  when running unchanged test bodies. This is full-operator validation, not
  complete vLLM/model integration or A3/A5 validation.
- Initial strong signed-input CPU oracle run: **14 pass, 7 fail on baseline**.
  Raw log/XML and the exact strong fixture source are retained. No threshold is
  widened. The final regression fixture keeps signed weights at the existing
  `1/fan_in` scale. The benchmark retains the stronger `1/sqrt(fan_in)` signed
  cases and compares candidate/reference outputs bitwise.
- Every benchmark warmup and measured sample is retained; all cases and
  slowdowns must be reported. Compare fresh-process baseline/candidate in ABBA
  order, pooling both complete repetitions rather than selecting best rounds.
- Check actual PID and exit files after transport/tool timeouts. Check NPU
  idle state before each device process, and save before/after snapshots.

## Primary references

- https://github.com/vllm-project/vllm-ascend/pull/9271
- https://github.com/vllm-project/vllm-ascend/pull/12896
- https://github.com/vllm-project/vllm-ascend/pull/16321
- https://github.com/vllm-project/vllm-ascend/pull/17054
- https://github.com/vllm-project/vllm-ascend/pull/15429

## Final scope decision

The reduction candidate is **rejected for general upstream use** and retained as
`rejected-kernel.patch`, not included in the PR. All 28 graph cases are preserved:
11 faster, 17 slower; geometric mean speedup 1.00351498. Graph latency changes
range from -9.46% to +3.81%. The eager measurements have substantial host noise:
10 faster, 18 slower, geometric mean speedup 0.96908505; those results are also
retained, without treating noise as evidence for a speedup or an exact regression.

The PR contains only original numerical regression tests, a reproducible
full-HcPre benchmark and its documentation. Final tests additionally cover
finite iteration counts 1, 3 and 20. Existing thresholds and all original test
cases are preserved. No model or operator runtime code is changed.

The captured graph contains 20 complete HcPre calls; event and synchronized wall
samples are divided by 20. Each graph output is bitwise checked against the
eager baseline. Graph replay wall latency is not eager invocation wall latency.
