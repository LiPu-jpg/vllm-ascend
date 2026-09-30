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

The contiguous Cast candidate combines row conversions only when both source
and destination row strides equal the logical width. Padded rows retain their
original conversions. This preserves dtype, rounding modes, synchronization,
FP32 reductions and the requested Sinkhorn iteration count. Stage 1 input
conversion and Stage 2 residual-stream conversion use the helper. Fewer source
API calls do not establish fewer emitted instructions or a shorter critical
path. This candidate is excluded from the contribution after matched NPU
measurements: graph ABBA and BAAB geometric mean speedups are 0.978565531 and
0.994634162. Eager process pairs disagree in direction. Normal nightly passes
41/41 per variant, while boundary failures remain retained. No stable latency
gain or model throughput improvement is established. See the
[complete immutable evidence](https://github.com/LiPu-jpg/vllm-ascend/tree/b6bfe2644fef2f6ff02198b94dbe650f37fdf882/contribution-evidence-hc-pre-20260930/runtime-iteration-04)
for every case, sample, slowdown, correctness failure and profiling result.
