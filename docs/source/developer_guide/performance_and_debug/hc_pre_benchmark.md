# HcPre operator benchmark

`benchmarks/hc_pre.py` measures the complete fused operator through the installed
plugin. V2 is used by GLM5Next and DeepSeek V4; V3 also returns mixing coefficients
and supports external coefficients. Compare the same API across revisions.
V2-versus-V3 timings are not a baseline comparison.

For example, run each installed revision in a fresh process:

```bash
python benchmarks/hc_pre.py --api v2 --timing graph --graph-batch 32 \
    --warmup 10 --samples 25 --rounds 3 --label baseline --output /tmp/hc-pre-baseline
python benchmarks/hc_pre.py --api v2 --timing graph --graph-batch 32 \
    --warmup 10 --samples 25 --rounds 3 --label candidate --output /tmp/hc-pre-candidate \
    --reference /tmp/hc-pre-baseline
```

Use the same hardware, dependencies, build flags, runtime configuration and
inputs. Verify that each process loads its intended installed OPP package and
kernel object. Check other jobs before and after each process. Use ABBA and
reverse ordering with an A/A control; preserve every shape, sample, warmup,
slowdown and process result. Report process and round variation alongside
pooled medians. The default shapes include decode and prefill batches, odd token
counts and both supported hidden sizes. Signed inputs stress cancellation; this
benchmark checks baseline byte parity rather than CPU accuracy. The nightly
operator tests provide the CPU accuracy checks with finite iteration counts.

`event` times eager calls. `graph` captures `--replays` complete calls per graph
and enqueues `--graph-batch` replays between external NPU events. Both event and
synchronized host wall times are divided by the number of complete calls.
Queuing multiple replays amortizes host submission gaps; report it separately
from single-replay measurements. Preserve profiling diagnostics separately from
benchmark samples. None of these timings measure model throughput.

The short-vector Div candidate uses one masked repeat when the broadcasted
element count fits one vector repeat. Longer vectors retain the count API.
It preserves exact division, dtype, broadcast padding, FP32 reductions and
the requested Sinkhorn iteration count. Softmax and each Sinkhorn row
normalization use the helper; GLM5Next and DeepSeek V4 are actual callers.
Normal-nightly cases include hidden sizes 128/4096/7168 and odd token batches
to exercise both short-vector selection and fallback. Correctness, performance
and final model integration remain unverified for this candidate.

The installed CANN 9.1.0 implementation uses different mask control sequences
for these overloads. This is an optimization hypothesis, not proof of fewer
emitted instructions or a shorter critical path. See the official
[Div API](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/memory_vector_compute/basic_arithmetic/Div.md)
for the masked-repeat and total-count interfaces.
