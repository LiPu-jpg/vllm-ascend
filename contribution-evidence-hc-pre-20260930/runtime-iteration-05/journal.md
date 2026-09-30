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

## Actual start after the other task completed

SFA controller1372465 is terminal (actual /proc observation), its log has
Third candidate and rebuilt-control experiment complete, and foreign_jobs
returns[] after checking real processes. Only then starter --stage2 launched
our controller1408363. Same actual PID must be observed on timeout, not
restarted. Initial own waiter1377608 remains terminal/cancelled, not successful.
Iteration05 inputs scanned by gitleaks with no findings. Controller-v2 initial
foreign-before-env is[]; actual build progress and eventual device guards
must be verified separately. No candidate NPU outcome is claimed yet.

Actual controller1408363 and build child1408479 are live, compiling protobuf
with real cc1plus descendants. The official build command retains vendor
cast_baseline/cast_candidate in the NEW short-div-source directories.
An unexecuted validation path had incorrectly expected short_div vendors;
corrected it to the actual generated cast_VARIANT_transformer paths while
only the build is active. Original driver and before/after hashes are
retained. No build, runtime source, compiler options or measured cohort
was modified, and no restart occurred. Build/validation remain pending.

Baseline complete native/OPP build passed at a40b52d. Native extension
f8c4b086495f7c609f86f0cb0765e17e8dca404d356124c641eca3baacb5169b;
direct kernels eebb909c05e51a0c6707097405abde63643448c33a718c0aa55ff533eaf01f50;
HcPre object e4fe3ba278578281a0bb142d5da21cbfeb6d55e355378112fc429440eea23622.
Candidate build is still actually active. Before any NPU validation, amended
unexecuted run_validation.sh to check first timed baseline/candidate kernel
selection in separate LD_PRELOAD subprocesses with fresh private diagnostic
caches. Actual object path/hash must match built manifest. Timed processes
have no instrumentation. Original driver and before/after hashes preserved;
runtime source, build flags and frozen benchmark are unchanged.

## Completed builds and retained baseline nightly failures

Both immutable full builds succeeded. Baseline normal nightly77:65 passed,12 failed; failures are Y CPU accuracy for hidden128, batch257 or3x17, both signed inputs and finite iterations1/3/20. Original controller1408363 terminal exit1; no performance cohort ran. New controller-v5 reuses builds and records candidate same77, preserving both XMLs; never rewrites v2 status. Candidate outcome pending.

Added a separate diagnostic driver for all72 frozen parameter fixtures. It records all four CPU outputs, exact V2/V3/repeat/graph/input parity and cross-process baseline comparison; it does not modify the frozen nightly file or thresholds. All failures remain failures.

## Same-suite and all-output diagnostics completed

Controller1420960(v5) terminal0 means complete comparison recorded, NOT tests passed. Candidate nightly exit1,65/77 pass12 fail, same failing names as baseline. Controller1421212(v6) terminal0 similarly records both diagnostic failures. All72 fixtures:60 CPU/byte-parity pass each;48/48 hidden4096/7168 pass both. In the12 hidden128 batch257/3x17 cases all four V3 outputs and all three V2 outputs fail CPU thresholds. Baseline and candidate post outputs differ between repeat,V3 andgraph in those12;candidate has one additional cross-process V3 post difference in the same already-unstable set. No acceptance is inferred.

Controller1421700(v7) started only after actual prior PID terminal and foreign guard[]. Runs retained60 boundarycases,24 actual callercases then all28 performancecases in graph ABBA,A/A,BAAB and event ABBA,A/A. It has no profiling instrumentation in timing. Initial boundary baseline57/60 CPU pass,candidate57/60 CPU pass;candidate has6crossprocess byte differences. These remain failures, not pass or acceleration proof.

## Current source overlap and first pair

Latest upstream62e05feb3db521230c27714ad4347bd0d9d38f1a is one MLA draft-metadata fix after frozen a40. Git diff shows no changes in HcPre,binding,GLM orDeepSeek model files. Existing coherent cohorts remain frozen at a40/21d;final rebase/integration still required if accepted. PR17054 remainsOPEN head33bfef419bc4dbe679582011104beca9112373be. Its batched comb loop still calls DivABLastDimBrcInline and does not add the same short-count masked-repeat branch. All28 first-pair graph cases completed:1.0103201492619827 geometricmean24fast4slow maxslowdown2.1866344522756487%. This is one independent pair only,NOT acceptance/stable/modelgain. Actual private kernel opens match both build hashes.

Prepared unstarted controller-v8 for L1 trace/eager/graph and standarddummy modelseager/graph, requires v7terminal0 plusitscompletionmarker;no waitloop. It will apply the same independent17828 prerequisite onlyafter timing,recordprivate source diffs,and preserveall prior failures.

## First complete ABBA result, candidate not accepted

All28 cases, two independent processes perarm,75 measuredsamples perprocess/case and150 pooledperarm/case. Geometricmean0.995288552144213;independentpairs1.0103201492619827 and0.9785921499397137;10faster18slower,maxslowdown4.05567835546965%. No confidenceinterval ormodelgain claimed. The first positivepair is not substituted for the complete cohort. All case/sample/round results retained in completed/graph-abba-summary.json and four unchanged results.json reports.

Original controller1421700 still actually live;child1423645 is processing div2-graph-aa-a1. No restart. A/A,BAAB,eventABBA,eventA/A remaininprogress;prepared profiles/modelstage is unstarted. Current conclusion: stablebenefit unproven, runtimePRnotready.

## Foreign-after guard stopped controller-v7

Actual original controller1421700 is terminal,exit1. The initial A/A div2-graph-aa-a1 benchmark wrote all28 cases,then failed its foreign-after guard: SFA controller1423682 started. Saved npu-after has noNPUprocess,foreign-after identifiesitscontroller;this does not prove nooverlap throughout the arm. Retain all data but do not count this arm as a clean guarded A/A cohort. Do not infer a transportfailure or restart. Current foreignPID1423682 is live,so noowncontrollerstarted. Prepared unstartedcontroller9 usesnewdiv4labelsforfreshA/A,BAAB,eventABBA,eventA/A andrequiresactualoldterminalstate plusbeforelaunchforeignguard. Controller10profiles/models requires9success. No backgroundwaiter orremote build whileotherowneractive.

## Recovered controls started after verified free window

Foreign1423682/1425003 both terminal inactualps query,and authoritativeforeignguard[]. Preflight verifiesNPU3 Ascend910B3 healthOK37C andnorunningprocess. Frozenbaselinea40/candidate21d unchanged;onlyuntrackedprivateopp buildoutputs. Starterlaunchednewcontroller1427028(v9),notrestartv7oroverwriteoldlabels. SameactualPIDmustbeobservedontransporttimeout. Newsource5hoistcandidate b3cbc06/localiteration06preparedonly;noglobalinstallorconcurrentcloudbuild. FullstagedformatciandDCOcommitforkpushpassed;itsNPUoutcomeunverified.

## All recovered controls complete; October1 continuation

Controller1427028(v9) terminal0, SHORT_DIV_RECOVERED_ORDER_CONTROLS_COMPLETE. All16 div4 arms downloaded with before/after foreign[] and no NPU process, run.exit0. Graph ABBA0.995288552144213 (10fast18slow,max slowdown4.055678%), BAAB0.9877529453485497 (5fast23slow,max5.484968%), graph AA0.9630107639854758 (0fast28slow,max7.170879%). Event ABBA1.067104549743223 pairs1.0073294452127934/1.1052490067848808; event AA0.9752871222094138. Every28case and all150samples perarm retained. No stable Div improvement established. V10 profiles/models remains unstarted: actual new SFA1463771/edges1464774 are live. No restart or own build. Independent prefetch source b712c2b2bda7603af7ec5c3386726ff30979a2b5 is locally committed, full formatci passed; NPU outcome unverified.
