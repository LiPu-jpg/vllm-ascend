# HcPre short-vector Div validation status

Candidate: `21d7920f51a71cedd1500ac95929d44031cbaafd`.
Baseline: `a40b52df0ef06a6360e2e97ce9b37a8939240d3f`.
The candidate is on a separate fork branch; PR17821 still contains only tests,
benchmark and documentation. No operator or model acceleration is established.

The change replaces count-mode Div with one masked vector repeat only when the
padded vector fits one hardware repeat. Broadcast, barriers, arithmetic, dtype,
reductions, eps and finite iteration count stay unchanged. GLM and DeepSeekV4
call the affected complete HcPre operation. No competition source was copied.

Both fresh full native/OPP builds succeeded with matching build configuration.
Normal nightly collection: baseline65/77 pass and candidate65/77 pass. Both
fail the same12 hidden128, batch257/3x17, signed/unsigned, iteration1/3/20 cases.
These failures are retained and are not counted as passing.

A separate full-plugin diagnostic executed all72 parameter fixtures without
short-circuiting at the first CPU assertion. Both have60 passing fixtures;
all48 hidden4096/7168 fixtures pass CPU accuracy and repeat/V2/V3/graph/input
checks. Candidate outputs match the baseline byte for byte in those48.
The12 small-hidden failures affect every CPU output. Post also varies between
repeat,V3 and graph on the baseline and candidate. One candidate cross-process
V3 post mismatch occurs in the same unstable failed-case set. This does not
establish a unique root cause or full candidate equivalence.

Boundary60: each arm has57 CPU passes and3 CPU failures. Candidate additionally
has6 cross-process output mismatch cases. All are retained. These are new
cohorts on the stated baseline and must not be substituted for prior cohorts.

The actual decoder caller and complete-operator timing controller1421700 is
running. It checks idle NPU and foreign tasks before each launch, uses all28
benchmark fixtures, graph ABBA/A/A/BAAB and eager ABBA/A/A, and retains every
sample. Actual private kernel selection is checked in a separate process before
timing. No tracer is present in measured timing processes. Performance, L1
profiles and standard-loader model verification remain unfinished.

A terminal comparison controller exit0 means all results were recorded; the
individual nightly/diagnostic exits are1 and remain test failures. Original
controller1408363 retains exit1. It was not rebuilt or restarted.

The first complete graph ABBA now pools150 measured samples per arm/case.
All28 cases are retained: geometric mean speedup0.995288552144213,10 faster,
18 slower,max slowdown4.05567835546965%. Independent pair means are
1.0103201492619827 and0.9785921499397137. No stable benefit or candidate
acceptance is established. The same controller is now running A/A controls.

## Current status, October1

All recovered controls complete. The earlier live-PID paragraphs above are historical snapshots. V9 actualPID1427028 terminal0. Graph ABBA0.995288552144213 and BAAB0.9877529453485497 do not establish gain; same-code graph AA0.9630107639854758 shows substantial order/process variation. Event ABBA1.067104549743223 disagrees between pairs, event AA0.9752871222094138. All cases, slower results and raw samples remain. V10 profiling/model stage has not started because foreign SFA controller1463771 and edges1464774 are live. No transport failure or restart inferred. PR17821 remains tests/benchmark/docs only; overall runtime contribution unfinished.
