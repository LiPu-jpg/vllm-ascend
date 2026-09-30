# Single-repeat short Div candidate

Previous goal turn: progress. All iteration-04 terminal controls, model graph
proof and profiles were analyzed; contiguous Cast was rejected, all text
evidence DCO-signed/pushed at b6bfe2644fef2f6ff02198b94dbe650f37fdf882 and
PR #17821 updated with the three rejected/unproved candidates. Goal active.

## Hypothesis

Repeated short row-normalization Div calls enter/exit count-mask mode in the
CANN 9.1.0 dav_c220 implementation, regardless of small count. For a positive
count fitting one vector repeat, the continuous-mask overload emits the same
Div intrinsic with identical contiguous strides without changing count mode.
Use it in DivABLastDimBrcInline, preserving broadcast, PipeBarrier, dtype,
padding, exact divisions, FP32 reductions and finite iteration counts. Longer
vectors and all other helper branches retain the existing implementation.

This generic single-repeat selection is based on hardware vector capacity,
not benchmark shapes. GLM5Next and DeepSeek V4 real mHC callers use n=4;
Stage 2 SoftmaxFP32Perf and each of the requested Sinkhorn row iterations
call the helper. Its existing multi-column branch already leaves the last
normal-mode mask; every subsequent vector call in the current callers sets
its own mask. No isSetMask=false call is introduced. Mask state and byte
parity still need NPU validation.

Competition source 4546d1864b3a16da3fc8bfe5ad3b06de380526bd contains repeat/
mask vector arithmetic. Its missing LICENSE forbids copying that source;
this independent nine-line implementation only applies the generic API
selection idea and retains the existing CANN OSLA 2.0 header.

SDK inspected:
compiler/tikcpp/tikcfw/impl/dav_c220/kernel_operator_vec_binary_impl.h
DivImpl count lines213-225 enters count mode, sets total count, issues vdiv,
restores normal mode/full mask; continuous-mask lines201-209 sets the normal
mask and invokes DivIntrinsicsImpl. No emitted-ISA counts or speedup are
claimed from this source/API analysis. Official API:
https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Div.md

## Current source and checks

Independent branch codex/hc-pre-short-div-20260930 at 21d7920f51a71cedd1500ac95929d44031cbaafd,
base a40b52df0ef06a6360e2e97ce9b37a8939240d3f (latest inspected main).
HcPre, binding and CMake show no diff from iteration-04 baseline11682d1.
Only root AGENTS applies, SHA256 dc198b13b3dea93f57883b2c7bedb44ad693b83f5e7e74a3b7f2b558eceae97a.
Full format.sh ci and source git diff --check passed. DCO Signed-off-by.
Normal-nightly fixture has original five plus 72 finite-iteration/signed/
V2-V3/input-preservation/graph cases. Added hidden128 and tokens257 cover
short vectors and the longer-vector fallback; original thresholds unchanged.
No candidate correctness or performance has been established.

## Device protection and next gate

NPU3 reports910B3/healthOK, no NPU processes at initial read. Other SFA
controller1372465 is actually live with child1376951 paired.py using NPU.
No HcPre compilation or NPU run is started concurrently. The new controller
will wait for live foreign jobs to terminate before building. Do not modify
other sources, environment, dependencies or processes. First compile matched
private OPP packages and inspect intended kernels. Complete native/plugin
checks and actual model validation remain required before acceptance.

## Own waiter cancelled before any build

The uploaded bundle SHA256 ee670f7f668ffa79afdbbf27e22a9db344b2c090cb3d6b8688f8fd7787ddc6a3
was independently verified on cloud; Git bundle verification requires existing
11682d1 and passed in cast-source-candidate. Fork branch points to21d7920.
Our new controller1377608 was actually live in its foreign-job wait, but SFA
current-window.json identifies it as a foreign controller. This produced
mutual waiting. The actual own process group and command were inspected,
and build.log absence proved no build started. Only our isolated unstarted
waiter was terminated deliberately; this is not a timeout-triggered restart.
No other process, environment or source was modified. Initial ATB environment
setup spawned a short CPU-only torch ABI query before the guard; move ATB
setup after the idle gate for subsequent controller versions. Do not leave
a background waiter that blocks the other owner's guard. Continue local
preparation and observe the actual other controller until terminal.

Initial waiter exited0 after cancellation, but has no build log or completion
marker; it is explicitly cancelled, not successful. Controller-v2 is the
first actual build/validation stage, unstarted. The starter checks actual
foreign jobs BEFORE spawning it, and has no automatic restart. Subsequent
stages are unstarted and require predecessor exit0 plus its exact completion
marker. Only launch them after inspecting that predecessor's actual terminal
process state. Normal fixture has77 cases including the original five.
Tracked benchmark and frozen driver both SHA256
011144fd9193fe946979eda950ec5e8a94ee9ee03a60aa4839cef68351239076.
Documentation/benchmark commit a1f70b860f4eb08d5f34e5d734a81d2275745fb6
passed full format.sh ci and was pushed. Runtime/kernel/test build ref stays
21d7920. Candidate correctness, performance, full builds and models remain
unverified; nothing has been added to test PR17821.
