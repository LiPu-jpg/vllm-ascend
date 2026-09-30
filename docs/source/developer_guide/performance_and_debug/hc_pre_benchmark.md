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

The input-prefetch candidate changes the AIV stage's input schedule. It queues
one input tile before the row loop, queues the next hidden tile after dequeuing
the current tile, and queues the next row's first tile before the post gate and
Sinkhorn stages. The existing two input buffers are reused. Queue depth remains
one: the current tensor is dequeued before the next tensor is enqueued. No new
buffer, tiling condition or arithmetic operation is introduced. The arch35
implementation is unchanged.

The intended benefit is earlier input DMA submission while vector computation
consumes the current buffer. The existing queue framework may already overlap
parts of the original loop; double buffering alone does not establish a gain.
Compare complete-operator latency and L1 pipeline diagnostics to determine
whether the schedule shortens the critical path. Projection, gate formulas,
FP32 reductions, epsilon placement, finite Sinkhorn iterations and output
contracts are unchanged. Nightly coverage includes graph replay after updating
activations, both hidden sizes, signed inputs and row tails.

This candidate has not yet been built or tested on NPU. No operator or model
speedup is established. Preserve known baseline numerical failures and compare
them separately; passing byte parity does not replace CPU accuracy checks.
