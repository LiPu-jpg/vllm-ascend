# HcPre operator benchmark

`benchmarks/hc_pre.py` measures the complete fused operator through the installed
plugin. V2 is used by GLM5Next and DeepSeek V4; V3 also returns the optional
mixing coefficients and supports external coefficients. Compare the same API
across revisions. V2-versus-V3 timings are not a baseline comparison.

For example, run each installed revision in a fresh process:

```bash
python benchmarks/hc_pre.py --api v2 --timing graph --graph-batch 32 \
    --warmup 10 --samples 25 --rounds 3 --label baseline --output /tmp/hc-pre-baseline
python benchmarks/hc_pre.py --api v2 --timing graph --graph-batch 32 \
    --warmup 10 --samples 25 --rounds 3 --label candidate --output /tmp/hc-pre-candidate \
    --reference /tmp/hc-pre-baseline
```

Use the same hardware, dependencies, runtime configuration, OPP package and
inputs. Check that other jobs are idle before and after each process. Use ABBA
ordering and an A/A control; preserve every shape, sample, warmup, slowdown and
process result. The default shapes include decode batches, prefill batches,
odd token counts and both supported hidden sizes. Signed inputs stress
cancellation; this benchmark checks baseline byte parity rather than CPU accuracy.
The nightly operator tests provide the CPU accuracy checks.

`event` times eager calls. `graph` captures `--replays` complete calls per graph
and enqueues `--graph-batch` replays between external NPU events. Both event and
synchronized host wall times are divided by the total number of calls. Queuing
multiple replays amortizes host submission gaps; report it separately from
single-replay measurements. Allocation savings during eager dispatch or capture
need separate host-side evidence. None of these timings measure model throughput.

The V2 binding can omit the optional `pre` output because its public result has
only three tensors. The kernel still computes mixing coefficients internally;
the intended savings are the unused allocation and its device writeback, without
changing FP32 reductions or the requested Sinkhorn iteration count. Performance
of this candidate is currently unvalidated.
