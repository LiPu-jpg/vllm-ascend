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
operator tests provide CPU accuracy checks with finite iteration counts.

`event` times eager calls. `graph` captures `--replays` complete calls per graph
and enqueues `--graph-batch` replays between external NPU events. Both event and
synchronized host wall times are divided by the number of complete calls.
Queuing multiple replays amortizes host submission gaps; report it separately
from single-replay measurements. Preserve profiling diagnostics separately from
benchmark samples. None of these timings measure model throughput.

The comb-copy candidate batches input DMA across Cube partials. The original
comb stage submits one copy per partial and token, with one block per matrix row.
The candidate submits one copy per matrix row and token, with one block per
partial. It keeps the UB layout `[partial][token][matrix row][aligned column]`
and uses the original traversal when the partial count does not exceed the
matrix width, or the DMA count or strides exceed the API limits.

For 32 partials and matrix width 4, the source submits 4 rather than 32 copies
per token. This is an API submission count, not a measured instruction count or
latency reduction. The emitted DMA operations and complete-operator critical
path require profiling. No new UB buffer, arithmetic, tiling parameter or public
API is introduced; the arch35 implementation is unchanged.

Valid-element address equality does not establish byte equality of dummy
padding. `DataCopyPad` with padding disabled may fill alignment lanes from copied
data, and grouping can affect those lanes. Check all production outputs on NPU,
including signed inputs, tails, graph replay and external mixing coefficients.
Keep CPU accuracy checks separate from baseline parity. The iteration count,
epsilon placement and precision thresholds must stay unchanged.

This candidate has not yet been built or tested on NPU. No operator or model
speedup is established. Preserve known baseline numerical failures alongside
candidate results.
